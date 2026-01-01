import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import json
from mlxtend.frequent_patterns import apriori, association_rules
import warnings
import os
import traceback
from datetime import datetime
import time
import gzip
import functools
from collections import defaultdict

warnings.filterwarnings('ignore')

def cache_response(max_age=300, compress=True):
    """Decorator for caching and compressing responses"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                response = make_response(f(*args, **kwargs))
                response.headers['Cache-Control'] = f'public, max-age={max_age}'
                if compress and 'Accept-Encoding' in request.headers and 'gzip' in request.headers['Accept-Encoding']:
                    response.data = gzip.compress(response.data)
                    response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response
            except Exception as e:
                return make_response(jsonify({"success": False, "error": str(e)}), 500)
        return decorated_function
    return decorator

def extract_datetime_features(df):
    """Extract datetime features from dataset"""
    df_clean = df.copy()
    
    if 'InvoiceDate' in df_clean.columns:
        try:
            df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'], errors='coerce')
            df_clean['Year'] = df_clean['InvoiceDate'].dt.year.fillna(2024).astype(int)
            df_clean['Month'] = df_clean['InvoiceDate'].dt.month.fillna(1).astype(int)
            df_clean['Day'] = df_clean['InvoiceDate'].dt.day.fillna(1).astype(int)
            df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour.fillna(12).astype(int)
            df_clean['Weekday'] = df_clean['InvoiceDate'].dt.day_name().fillna('Monday')
            df_clean['Weekday_Num'] = df_clean['InvoiceDate'].dt.dayofweek.fillna(0).astype(int)
            print(f"✓ Parsed InvoiceDate successfully")
        except Exception as e:
            print(f"⚠ Error parsing InvoiceDate: {e}")
            df_clean['Year'] = 2024
            df_clean['Month'] = 1
            df_clean['Day'] = 1
            df_clean['Hour'] = 12
            df_clean['Weekday'] = 'Monday'
            df_clean['Weekday_Num'] = 0
    else:
        print("⚠ InvoiceDate column not found")
        df_clean['Year'] = 2024
        df_clean['Month'] = 1
        df_clean['Day'] = 1
        df_clean['Hour'] = 12
        df_clean['Weekday'] = 'Monday'
        df_clean['Weekday_Num'] = 0
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_clean['Month_Name'] = df_clean['Month'].apply(lambda x: month_names[x-1] if 1 <= x <= 12 else 'Unknown')
    
    return df_clean

def apply_filters(df, filters):
    """Apply filters to dataframe"""
    df_filtered = df.copy()
    
    if 'country' in filters and filters['country'] and filters['country'] != 'all':
        if filters['country'].lower() != 'unknown':
            df_filtered = df_filtered[df_filtered['Country'] == filters['country']]
    
    if 'year' in filters and filters['year'] and filters['year'] != 'all':
        df_filtered = df_filtered[df_filtered['Year'] == int(filters['year'])]
    
    if 'month' in filters and filters['month'] and filters['month'] != 'all':
        df_filtered = df_filtered[df_filtered['Month'] == int(filters['month'])]
    
    if 'hour' in filters and filters['hour'] and filters['hour'] != 'all':
        df_filtered = df_filtered[df_filtered['Hour'] == int(filters['hour'])]
    
    if 'product' in filters and filters['product'] and filters['product'] != 'all':
        product_filter = filters['product'].lower().strip()
        if product_filter:
            df_filtered = df_filtered[df_filtered['Description'].str.lower().str.contains(product_filter, na=False)]
    
    if 'weekday' in filters and filters['weekday'] and filters['weekday'] != 'all':
        df_filtered = df_filtered[df_filtered['Weekday'] == filters['weekday']]
    
    return df_filtered

def remove_duplicate_rules(rules_df):
    """Remove duplicate rules (A→B and B→A) keeping the one with higher confidence"""
    if len(rules_df) == 0:
        return rules_df
    
    rules_dict = {}
    
    for idx, rule in rules_df.iterrows():
        antecedents = frozenset(rule['antecedents'])
        consequents = frozenset(rule['consequents'])
        
        # Create both possible keys
        key1 = (antecedents, consequents)
        key2 = (consequents, antecedents)
        
        # Store the rule with higher confidence
        if key1 in rules_dict:
            if rule['confidence'] > rules_dict[key1]['confidence']:
                rules_dict[key1] = rule
        elif key2 in rules_dict:
            if rule['confidence'] > rules_dict[key2]['confidence']:
                rules_dict[key2] = rule
        else:
            rules_dict[key1] = rule
    
    # Convert back to DataFrame
    unique_rules = pd.DataFrame(list(rules_dict.values()))
    return unique_rules

def calculate_product_stats(product_name, df_filtered):
    """Calculate detailed statistics for a product"""
    product_df = df_filtered[df_filtered['Description'] == product_name]
    
    if len(product_df) == 0:
        return None
    
    stats = {
        'total_quantity': int(product_df['Quantity'].sum()),
        'total_revenue': float(product_df['TotalAmount'].sum()),
        'avg_price': float(product_df['UnitPrice'].mean()),
        'transaction_count': int(product_df['InvoiceNo'].nunique()),
        'customer_count': int(product_df['CustomerID'].nunique()),
        'avg_quantity_per_transaction': float(product_df.groupby('InvoiceNo')['Quantity'].sum().mean()),
        'peak_hour': int(product_df['Hour'].mode().iloc[0] if not product_df['Hour'].mode().empty else 12),
        'most_common_weekday': str(product_df['Weekday'].mode().iloc[0] if not product_df['Weekday'].mode().empty else 'Monday'),
        'most_common_month': int(product_df['Month'].mode().iloc[0] if not product_df['Month'].mode().empty else 1),
        'top_country': str(product_df['Country'].mode().iloc[0] if not product_df['Country'].mode().empty else 'Unknown')
    }
    
    return stats

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:5000"])

df = None

def load_data():
    """Load data once at startup"""
    global df
    print("Loading data for Intelligent Product Assortment Dashboard...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        data_path = os.path.join(project_root, 'data', 'Online_Retail_Cleaned.csv')
        
        if not os.path.exists(data_path):
            # Try alternative paths
            alternative_paths = [
                os.path.join(current_dir, 'data', 'Online_Retail_Cleaned.csv'),
                os.path.join(current_dir, 'Online_Retail_Cleaned.csv'),
                'Online_Retail_Cleaned.csv'
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    data_path = alt_path
                    break
        
        if os.path.exists(data_path):
            print(f"📂 Loading data from: {data_path}")
            try:
                df = pd.read_csv(data_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(data_path, encoding='latin1')
                except Exception as e:
                    print(f"❌ Error reading CSV: {e}")
                    raise
            
            print(f"✅ CSV loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
            
            # Check required columns
            required_columns = ['InvoiceNo', 'Description', 'Quantity', 'UnitPrice']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"❌ Missing required columns: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clean and prepare data
            df = df.copy()
            
            # Clean critical columns
            if 'Description' in df.columns:
                df['Description'] = df['Description'].astype(str).str.strip()
                df = df[df['Description'] != '']
                df = df[df['Description'] != 'nan']
                df = df[~df['Description'].isnull()]
                print(f"✅ Cleaned Descriptions: {df['Description'].nunique():,} unique products")
            
            # Convert numeric columns
            if 'Quantity' in df.columns:
                df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
                df = df[df['Quantity'] > 0]
                df['Quantity'] = df['Quantity'].astype(int)
            
            if 'UnitPrice' in df.columns:
                df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
                df = df[df['UnitPrice'] > 0]
            
            # Calculate total amount
            df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
            
            # Extract datetime features
            df = extract_datetime_features(df)
            
            # Fill missing values
            if 'CustomerID' in df.columns:
                df['CustomerID'] = df['CustomerID'].fillna('Unknown').astype(str)
            
            if 'Country' in df.columns:
                df['Country'] = df['Country'].fillna('Unknown').astype(str)
            
            print(f"\n📊 FINAL DATASET STATS:")
            print(f"   Total Records: {len(df):,}")
            print(f"   Total Transactions: {df['InvoiceNo'].nunique():,}")
            print(f"   Total Products: {df['Description'].nunique():,}")
            print(f"   Total Revenue: ${df['TotalAmount'].sum():,.2f}")
            
            transaction_sizes = df.groupby('InvoiceNo').size()
            multi_item_count = (transaction_sizes > 1).sum()
            print(f"   Multi-item Transactions: {multi_item_count:,} ({multi_item_count/len(transaction_sizes)*100:.1f}%)")
            
        else:
            print(f"❌ ERROR: Data file not found at any expected location")
            print(f"   Searched in: {data_path}")
            raise FileNotFoundError(f"Data file not found. Please ensure 'Online_Retail_Cleaned.csv' is in the data directory.")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR loading data: {str(e)}")
        traceback.print_exc()
        raise

# Load data immediately
try:
    load_data()
except Exception as e:
    print(f"Failed to load data: {e}")
    df = pd.DataFrame()  # Create empty dataframe to prevent crashes

@app.route('/')
def home():
    return jsonify({
        "message": "Intelligent Product Assortment Dashboard API",
        "status": "running",
        "data_size": len(df) if df is not None else 0,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/health",
            "/api/summary",
            "/api/association_rules",
            "/api/suggested_bundles",
            "/api/revenue_analysis",
            "/api/seasonal_data",
            "/api/frequent_itemsets",
            "/api/top_products",
            "/api/filters",
            "/api/product_stats"
        ]
    })

@app.route('/api/health', methods=['GET'])
@cache_response(max_age=60)
def health_check():
    try:
        if df is None or len(df) == 0:
            return jsonify({
                "status": "unhealthy",
                "error": "Data not loaded",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "data_records": len(df),
            "transactions": df['InvoiceNo'].nunique(),
            "products": df['Description'].nunique(),
            "total_revenue": float(df['TotalAmount'].sum()),
            "memory_usage_mb": int(df.memory_usage(deep=True).sum() / 1024 / 1024)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/summary', methods=['GET'])
@cache_response(max_age=300)
def get_summary():
    """Get comprehensive data summary statistics"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        total_revenue = float(df['TotalAmount'].sum())
        total_transactions = int(df['InvoiceNo'].nunique())
        total_records = len(df)
        avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Calculate transaction size distribution
        transaction_sizes = df.groupby('InvoiceNo').size()
        multi_item_transactions = (transaction_sizes > 1).sum()
        multi_item_percentage = (multi_item_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        # Calculate basket size statistics
        basket_sizes = df.groupby('InvoiceNo')['Quantity'].sum()
        avg_basket_size = float(basket_sizes.mean())
        median_basket_size = float(basket_sizes.median())
        
        # Calculate product popularity
        product_counts = df['Description'].value_counts()
        top_10_products_percentage = (product_counts.head(10).sum() / product_counts.sum() * 100) if product_counts.sum() > 0 else 0
        
        # Calculate data quality metrics
        critical_columns = ['InvoiceNo', 'Description', 'Quantity', 'UnitPrice', 'CustomerID', 'Country']
        missing_counts = {}
        for col in critical_columns:
            if col in df.columns:
                missing_counts[col] = int(df[col].isnull().sum())
            else:
                missing_counts[col] = total_records
        
        total_critical_cells = len(df) * len(critical_columns)
        total_missing_critical = sum(missing_counts.values())
        data_completeness = round((1 - (total_missing_critical / total_critical_cells)) * 100, 2) if total_critical_cells > 0 else 0
        
        # Time range
        if 'InvoiceDate' in df.columns and df['InvoiceDate'].dtype == 'datetime64[ns]':
            min_date = df['InvoiceDate'].min()
            max_date = df['InvoiceDate'].max()
            date_range = {
                "start": min_date.strftime('%Y-%m-%d'),
                "end": max_date.strftime('%Y-%m-%d'),
                "days": (max_date - min_date).days
            }
        else:
            date_range = {
                "start": "Unknown",
                "end": "Unknown",
                "days": 0
            }
        
        summary = {
            "total_transactions": total_transactions,
            "total_products": int(df['Description'].nunique()),
            "total_customers": int(df['CustomerID'].nunique()) if 'CustomerID' in df.columns else 0,
            "total_revenue": total_revenue,
            "avg_transaction_value": round(avg_transaction_value, 2),
            "total_countries": int(df['Country'].nunique()) if 'Country' in df.columns else 0,
            "multi_item_percentage": round(multi_item_percentage, 1),
            "avg_basket_size": round(avg_basket_size, 2),
            "median_basket_size": round(median_basket_size, 2),
            "top_10_products_percentage": round(top_10_products_percentage, 1),
            "date_range": date_range,
            "data_quality": {
                "total_records": total_records,
                "data_completeness": data_completeness,
                "missing_customers": missing_counts.get('CustomerID', 0),
                "missing_descriptions": missing_counts.get('Description', 0),
                "missing_prices": missing_counts.get('UnitPrice', 0),
                "missing_quantities": missing_counts.get('Quantity', 0),
                "unique_products": int(df['Description'].nunique()),
                "unique_customers": int(df['CustomerID'].nunique()) if 'CustomerID' in df.columns else 0,
                "revenue_per_transaction": round(avg_transaction_value, 2),
                "multi_item_transactions": int(multi_item_transactions)
            }
        }
        
        return jsonify({
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error in summary: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/association_rules', methods=['GET'])
@cache_response(max_age=600)
def get_association_rules():
    """Get association rules"""
    try:
        start_time = time.time()
        
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Get parameters
        min_support = max(0.001, float(request.args.get('min_support', 0.01)))
        min_confidence = max(0.1, float(request.args.get('min_confidence', 0.3)))
        limit = min(100, int(request.args.get('limit', 50)))
        min_lift = float(request.args.get('min_lift', 1.0))
        simple = request.args.get('simple', 'true').lower() == 'true'
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all'),
            'weekday': request.args.get('weekday', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) < 100:
            return jsonify({
                "success": True,
                "data": [],
                "metadata": {
                    "note": f"Insufficient data after filtering ({len(filtered_df)} records). Try broader filters.",
                    "filtered_records": len(filtered_df),
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        # Get top products for analysis (limit to reasonable number)
        top_products = filtered_df['Description'].value_counts().head(50).index.tolist()
        df_top = filtered_df[filtered_df['Description'].isin(top_products)]
        
        if len(df_top) < 100:
            return jsonify({
                "success": True,
                "data": [],
                "metadata": {
                    "note": f"Insufficient transaction data after product filtering ({len(df_top)} records).",
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        try:
            # Create basket matrix
            basket = (df_top.groupby(['InvoiceNo', 'Description'])['Quantity']
                      .sum()
                      .unstack(fill_value=0)
                      .reset_index()
                      .set_index('InvoiceNo'))
            
            # Convert to boolean (bought or not)
            basket_sets = (basket > 0).astype(int)
            
            # Remove columns with very low frequency
            column_sums = basket_sets.sum()
            columns_to_keep = column_sums[column_sums >= 5].index.tolist()
            basket_sets = basket_sets[columns_to_keep]
            
            if len(basket_sets.columns) < 2:
                return jsonify({
                    "success": True,
                    "data": [],
                    "metadata": {
                        "note": "Not enough products with sufficient frequency for association analysis.",
                        "processing_time": round(time.time() - start_time, 2)
                    }
                })
            
            # Generate frequent itemsets
            frequent_itemsets = apriori(
                basket_sets, 
                min_support=min_support, 
                use_colnames=True,
                max_len=2,
                low_memory=True,
                verbose=0
            )
            
            if len(frequent_itemsets) == 0:
                # Try with lower support
                min_support = max(0.0005, min_support / 2)
                frequent_itemsets = apriori(
                    basket_sets, 
                    min_support=min_support, 
                    use_colnames=True,
                    max_len=2,
                    low_memory=True,
                    verbose=0
                )
            
            if len(frequent_itemsets) == 0:
                return jsonify({
                    "success": True,
                    "data": [],
                    "metadata": {
                        "note": f"No frequent itemsets found at {min_support*100:.2f}% support.",
                        "processing_time": round(time.time() - start_time, 2)
                    }
                })
            
            # Generate association rules
            rules = association_rules(
                frequent_itemsets, 
                metric="confidence", 
                min_threshold=min_confidence
            )
            
            # Filter by lift
            rules = rules[rules['lift'] >= min_lift]
            
            if len(rules) == 0:
                return jsonify({
                    "success": True,
                    "data": [],
                    "metadata": {
                        "note": f"No rules found with confidence >= {min_confidence} and lift >= {min_lift}.",
                        "processing_time": round(time.time() - start_time, 2)
                    }
                })
            
            # Sort by confidence and lift
            rules = rules.sort_values(['confidence', 'lift'], ascending=False)
            
            # Remove duplicate rules
            rules = remove_duplicate_rules(rules)
            
            # Format rules
            formatted_rules = []
            for idx, rule in rules.head(limit).iterrows():
                antecedents = list(rule['antecedents'])
                consequents = list(rule['consequents'])
                
                if antecedents and consequents:
                    antecedent_name = next(iter(antecedents))
                    consequent_name = next(iter(consequents))
                    
                    # Calculate additional metrics
                    antecedent_support = rule['antecedent support']
                    consequent_support = rule['consequent support']
                    leverage = rule['leverage']
                    conviction = rule['conviction']
                    
                    rule_data = {
                        "rule": f"{antecedent_name} → {consequent_name}",
                        "confidence": round(float(rule['confidence']), 3),
                        "lift": round(float(rule['lift']), 3),
                        "support": round(float(rule['support']), 4),
                        "antecedent": antecedent_name,
                        "consequent": consequent_name,
                        "antecedent_support": round(float(antecedent_support), 4),
                        "consequent_support": round(float(consequent_support), 4),
                        "leverage": round(float(leverage), 4),
                        "conviction": round(float(conviction), 3) if not pd.isna(conviction) else None
                    }
                    
                    if not simple:
                        rule_data.update({
                            "antecedents": antecedents,
                            "consequents": consequents
                        })
                    
                    formatted_rules.append(rule_data)
            
            processing_time = round(time.time() - start_time, 2)
            
            return jsonify({
                "success": True,
                "data": formatted_rules,
                "metadata": {
                    "total_rules_found": len(rules),
                    "rules_returned": len(formatted_rules),
                    "processing_time": processing_time,
                    "parameters": {
                        "min_support": min_support,
                        "min_confidence": min_confidence,
                        "min_lift": min_lift
                    },
                    "filter_stats": {
                        "original_records": len(df),
                        "filtered_records": len(filtered_df),
                        "products_in_analysis": len(basket_sets.columns),
                        "transactions_in_analysis": len(basket_sets)
                    }
                }
            })
            
        except Exception as algo_error:
            print(f"Algorithm error: {algo_error}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"Algorithm error: {str(algo_error)}",
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            }), 500
            
    except Exception as e:
        print(f"Error in association_rules: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/suggested_bundles', methods=['GET'])
@cache_response(max_age=600)
def get_suggested_bundles():
    """Generate suggested product bundles"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        min_confidence = max(0.1, float(request.args.get('min_confidence', 0.3)))
        limit = min(20, int(request.args.get('limit', 10)))
        min_transactions = max(2, int(request.args.get('min_transactions', 5)))
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all'),
            'weekday': request.args.get('weekday', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) < 100:
            return jsonify({
                "success": True,
                "bundles": [],
                "note": f"Insufficient data after filtering ({len(filtered_df)} records)."
            })
        
        bundles = []
        
        # Get top products
        top_products = filtered_df['Description'].value_counts().head(30).index.tolist()
        
        # Analyze pairs
        for i in range(len(top_products)):
            product1 = top_products[i]
            trans1 = set(filtered_df[filtered_df['Description'] == product1]['InvoiceNo'].unique())
            
            if len(trans1) < min_transactions:
                continue
            
            for j in range(i+1, min(i+10, len(top_products))):
                product2 = top_products[j]
                trans2 = set(filtered_df[filtered_df['Description'] == product2]['InvoiceNo'].unique())
                
                if len(trans2) < min_transactions:
                    continue
                
                common_trans = trans1.intersection(trans2)
                
                if len(common_trans) >= min_transactions:
                    confidence_1to2 = len(common_trans) / len(trans1) if len(trans1) > 0 else 0
                    confidence_2to1 = len(common_trans) / len(trans2) if len(trans2) > 0 else 0
                    confidence = max(confidence_1to2, confidence_2to1)
                    
                    if confidence >= min_confidence:
                        bundle_df = filtered_df[filtered_df['InvoiceNo'].isin(common_trans)]
                        bundle_products = filtered_df[filtered_df['InvoiceNo'].isin(common_trans)]['Description'].unique()
                        
                        # Calculate bundle metrics
                        bundle_revenue = bundle_df['TotalAmount'].sum()
                        avg_transaction_value = bundle_revenue / len(common_trans) if len(common_trans) > 0 else 0
                        
                        # Calculate lift
                        total_transactions = filtered_df['InvoiceNo'].nunique()
                        expected_cooccurrence = (len(trans1) * len(trans2)) / total_transactions if total_transactions > 0 else 0
                        lift = len(common_trans) / expected_cooccurrence if expected_cooccurrence > 0 else 1
                        
                        bundles.append({
                            "bundle_id": f"B{len(bundles)+1:03d}",
                            "products": [product1, product2],
                            "product_count": 2,
                            "bundle_name": f"{product1[:20]} & {product2[:20]}",
                            "confidence": round(confidence, 3),
                            "lift": round(lift, 2),
                            "estimated_revenue": float(bundle_revenue),
                            "avg_transaction_value": round(float(avg_transaction_value), 2),
                            "avg_product_price": float(filtered_df[filtered_df['Description'].isin([product1, product2])]['UnitPrice'].mean()),
                            "transaction_count": len(common_trans),
                            "popular_products_in_bundle": list(bundle_products[:5]) if len(bundle_products) > 0 else []
                        })
        
        # Sort by confidence and transaction count
        bundles.sort(key=lambda x: (x['confidence'], x['transaction_count']), reverse=True)
        
        return jsonify({
            "success": True,
            "bundles": bundles[:limit],
            "total_bundles_found": len(bundles),
            "metadata": {
                "min_confidence": min_confidence,
                "min_transactions": min_transactions,
                "filtered_records": len(filtered_df),
                "top_products_analyzed": len(top_products)
            }
        })
        
    except Exception as e:
        print(f"Error in suggested_bundles: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/revenue_analysis', methods=['GET'])
@cache_response(max_age=300)
def get_revenue_analysis():
    """Revenue analysis by country"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        limit = min(20, int(request.args.get('limit', 10)))
        
        # Analyze revenue by country
        if 'Country' in df.columns and 'TotalAmount' in df.columns:
            country_revenue = df.groupby('Country').agg({
                'TotalAmount': ['sum', 'mean', 'std'],
                'InvoiceNo': 'nunique',
                'CustomerID': 'nunique',
                'Description': 'nunique'
            }).round(2).reset_index()
            
            # Flatten column names
            country_revenue.columns = ['Country', 'total_revenue', 'avg_revenue', 'std_revenue', 
                                       'transaction_count', 'customer_count', 'product_variety']
            
            # Sort by total revenue
            country_revenue = country_revenue.sort_values('total_revenue', ascending=False)
            
            revenue_analysis = []
            for idx, row in country_revenue.head(limit).iterrows():
                country_df = df[df['Country'] == row['Country']]
                
                # Calculate additional metrics
                avg_transaction = country_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()
                revenue_per_customer = row['total_revenue'] / row['customer_count'] if row['customer_count'] > 0 else 0
                products_per_transaction = row['product_variety'] / row['transaction_count'] if row['transaction_count'] > 0 else 0
                
                revenue_analysis.append({
                    "country": row['Country'],
                    "total_revenue": float(row['total_revenue']),
                    "transaction_count": int(row['transaction_count']),
                    "customer_count": int(row['customer_count']),
                    "product_variety": int(row['product_variety']),
                    "avg_transaction_value": float(avg_transaction) if not pd.isna(avg_transaction) else 0.0,
                    "revenue_per_customer": round(float(revenue_per_customer), 2),
                    "products_per_transaction": round(float(products_per_transaction), 2),
                    "revenue_growth_potential": round(float(row['total_revenue'] * 1.15), 2),
                    "market_share": round((row['total_revenue'] / df['TotalAmount'].sum()) * 100, 2)
                })
        else:
            return jsonify({
                "success": False,
                "error": "Required columns (Country, TotalAmount) not found in data"
            }), 400
        
        return jsonify({
            "success": True,
            "revenue_analysis": revenue_analysis,
            "analysis_type": "country_revenue",
            "metadata": {
                "total_countries_analyzed": len(country_revenue),
                "global_total_revenue": float(df['TotalAmount'].sum()),
                "global_avg_transaction": float(df.groupby('InvoiceNo')['TotalAmount'].sum().mean())
            }
        })
        
    except Exception as e:
        print(f"Error in revenue_analysis: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/seasonal_data', methods=['GET'])
@cache_response(max_age=1800)
def get_seasonal_data():
    """Seasonal patterns analysis"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Monthly analysis
        monthly_data = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        month_stats = df.groupby('Month').agg({
            'TotalAmount': ['sum', 'mean', 'count'],
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique',
            'Description': 'nunique'
        }).round(2).reset_index()
        
        month_stats.columns = ['Month', 'total_revenue', 'avg_revenue', 'record_count', 
                               'transaction_count', 'customer_count', 'product_variety']
        
        for idx, row in month_stats.iterrows():
            month_df = df[df['Month'] == row['Month']]
            
            # Calculate transaction-level metrics
            transaction_values = month_df.groupby('InvoiceNo')['TotalAmount'].sum()
            
            monthly_data.append({
                "month": int(row['Month']),
                "month_name": month_names[row['Month'] - 1] if 1 <= row['Month'] <= 12 else 'Unknown',
                "revenue": float(row['total_revenue']),
                "transactions": int(row['transaction_count']),
                "customers": int(row['customer_count']),
                "product_variety": int(row['product_variety']),
                "avg_transaction": float(transaction_values.mean()) if not transaction_values.empty else 0.0,
                "median_transaction": float(transaction_values.median()) if not transaction_values.empty else 0.0,
                "records": int(row['record_count']),
                "revenue_share": round((row['total_revenue'] / df['TotalAmount'].sum()) * 100, 2)
            })
        
        # Hourly analysis
        hourly_data = []
        if 'Hour' in df.columns:
            hour_stats = df.groupby('Hour').agg({
                'TotalAmount': ['sum', 'mean', 'count'],
                'InvoiceNo': 'nunique'
            }).round(2).reset_index()
            
            hour_stats.columns = ['Hour', 'total_revenue', 'avg_revenue', 'record_count', 'transaction_count']
            
            for idx, row in hour_stats.iterrows():
                hourly_data.append({
                    "hour": int(row['Hour']),
                    "revenue": float(row['total_revenue']),
                    "transactions": int(row['transaction_count']),
                    "records": int(row['record_count']),
                    "avg_transaction": float(row['avg_revenue']),
                    "time_period": "Morning" if 6 <= row['Hour'] < 12 else 
                                  "Afternoon" if 12 <= row['Hour'] < 18 else 
                                  "Evening" if 18 <= row['Hour'] < 24 else "Night"
                })
        
        # Weekday analysis
        weekday_data = []
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if 'Weekday' in df.columns:
            weekday_stats = df.groupby('Weekday').agg({
                'TotalAmount': ['sum', 'mean', 'count'],
                'InvoiceNo': 'nunique',
                'CustomerID': 'nunique'
            }).round(2).reset_index()
            
            weekday_stats.columns = ['Weekday', 'total_revenue', 'avg_revenue', 'record_count', 
                                     'transaction_count', 'customer_count']
            
            # Sort by weekday order
            weekday_stats['Weekday'] = pd.Categorical(weekday_stats['Weekday'], categories=weekday_order, ordered=True)
            weekday_stats = weekday_stats.sort_values('Weekday')
            
            for idx, row in weekday_stats.iterrows():
                weekday_df = df[df['Weekday'] == row['Weekday']]
                transaction_values = weekday_df.groupby('InvoiceNo')['TotalAmount'].sum()
                
                weekday_data.append({
                    "weekday": row['Weekday'],
                    "weekday_num": weekday_order.index(row['Weekday']),
                    "revenue": float(row['total_revenue']),
                    "transactions": int(row['transaction_count']),
                    "customers": int(row['customer_count']),
                    "records": int(row['record_count']),
                    "avg_transaction": float(transaction_values.mean()) if not transaction_values.empty else 0.0,
                    "revenue_per_customer": float(row['total_revenue'] / row['customer_count']) if row['customer_count'] > 0 else 0
                })
        
        return jsonify({
            "success": True,
            "monthly_data": monthly_data,
            "hourly_data": hourly_data,
            "weekday_data": weekday_data,
            "metadata": {
                "total_months": len(monthly_data),
                "total_hours": len(hourly_data),
                "total_weekdays": len(weekday_data),
                "peak_month": max(monthly_data, key=lambda x: x['revenue'])['month_name'] if monthly_data else None,
                "peak_hour": max(hourly_data, key=lambda x: x['revenue'])['hour'] if hourly_data else None,
                "peak_weekday": max(weekday_data, key=lambda x: x['revenue'])['weekday'] if weekday_data else None
            }
        })
        
    except Exception as e:
        print(f"Error in seasonal_data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/frequent_itemsets', methods=['GET'])
@cache_response(max_age=600)
def get_frequent_itemsets():
    """Get frequent itemsets for network graph"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        min_support = max(0.001, float(request.args.get('min_support', 0.02)))
        limit = min(30, int(request.args.get('limit', 20)))
        
        # Get top products
        product_stats = df.groupby('Description').agg({
            'TotalAmount': 'sum',
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique'
        }).round(2).reset_index()
        
        product_stats.columns = ['Description', 'total_revenue', 'transaction_count', 'customer_count']
        top_products = product_stats.nlargest(limit, 'transaction_count')['Description'].tolist()
        
        nodes = []
        links = []
        
        # Create nodes
        for i, product in enumerate(top_products):
            product_info = product_stats[product_stats['Description'] == product].iloc[0]
            product_df = df[df['Description'] == product]
            
            # Calculate category based on price
            avg_price = product_df['UnitPrice'].mean()
            if avg_price < 10:
                category = "Low Price"
            elif avg_price < 50:
                category = "Medium Price"
            else:
                category = "High Price"
            
            # Calculate centrality metrics
            invoices_with_product = set(product_df['InvoiceNo'].unique())
            
            nodes.append({
                "id": f"P{i:03d}",
                "name": product[:30],
                "full_name": product,
                "group": category,
                "value": float(product_info['total_revenue'] / 1000),  # Value in thousands
                "revenue": float(product_info['total_revenue']),
                "transactions": int(product_info['transaction_count']),
                "customers": int(product_info['customer_count']),
                "avg_price": float(avg_price) if not pd.isna(avg_price) else 0.0,
                "degree": 0  # Will be updated when creating links
            })
        
        # Create links
        link_id = 0
        for i in range(len(nodes)):
            product1 = nodes[i]['full_name']
            invoices1 = set(df[df['Description'] == product1]['InvoiceNo'].unique())
            
            for j in range(i+1, min(i+15, len(nodes))):
                product2 = nodes[j]['full_name']
                invoices2 = set(df[df['Description'] == product2]['InvoiceNo'].unique())
                common_invoices = invoices1.intersection(invoices2)
                
                if common_invoices and len(common_invoices) >= 2:
                    # Calculate Jaccard similarity
                    jaccard = len(common_invoices) / len(invoices1.union(invoices2)) if len(invoices1.union(invoices2)) > 0 else 0
                    
                    # Calculate lift
                    total_transactions = df['InvoiceNo'].nunique()
                    expected_cooccurrence = (len(invoices1) * len(invoices2)) / total_transactions if total_transactions > 0 else 0
                    lift = len(common_invoices) / expected_cooccurrence if expected_cooccurrence > 0 else 1
                    
                    if jaccard >= 0.01:  # Minimum similarity threshold
                        links.append({
                            "id": f"L{link_id:04d}",
                            "source": nodes[i]['id'],
                            "target": nodes[j]['id'],
                            "source_name": nodes[i]['name'],
                            "target_name": nodes[j]['name'],
                            "value": float(jaccard),
                            "transactions": len(common_invoices),
                            "strength": float(lift),
                            "revenue": float(df[df['InvoiceNo'].isin(common_invoices)]['TotalAmount'].sum())
                        })
                        link_id += 1
                        
                        # Update node degrees
                        nodes[i]['degree'] += 1
                        nodes[j]['degree'] += 1
        
        return jsonify({
            "success": True,
            "network": {
                "nodes": nodes,
                "links": links
            },
            "metadata": {
                "nodes_count": len(nodes),
                "links_count": len(links),
                "min_support": min_support,
                "avg_node_degree": sum(node['degree'] for node in nodes) / len(nodes) if nodes else 0,
                "max_node_degree": max(node['degree'] for node in nodes) if nodes else 0
            }
        })
        
    except Exception as e:
        print(f"Error in frequent_itemsets: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/top_products', methods=['GET'])
@cache_response(max_age=300)
def get_top_products():
    """Get top products"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        limit = min(50, int(request.args.get('limit', 20)))
        sort_by = request.args.get('sort_by', 'revenue')  # revenue, transactions, customers
        
        # Apply filters if any
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        # Calculate product statistics
        product_stats = filtered_df.groupby('Description').agg({
            'TotalAmount': ['sum', 'mean', 'count'],
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique',
            'UnitPrice': 'mean',
            'Quantity': 'mean'
        }).round(2).reset_index()
        
        product_stats.columns = ['Description', 'total_revenue', 'avg_revenue', 'record_count', 
                                 'transaction_count', 'customer_count', 'avg_price', 'avg_quantity']
        
        # Sort based on parameter
        if sort_by == 'transactions':
            product_stats = product_stats.sort_values('transaction_count', ascending=False)
        elif sort_by == 'customers':
            product_stats = product_stats.sort_values('customer_count', ascending=False)
        else:  # revenue (default)
            product_stats = product_stats.sort_values('total_revenue', ascending=False)
        
        products_list = []
        for idx, row in product_stats.head(limit).iterrows():
            # Calculate additional metrics
            product_df = filtered_df[filtered_df['Description'] == row['Description']]
            
            # Calculate return customer rate
            return_customers = product_df.groupby('CustomerID').size()
            return_customer_rate = (len(return_customers[return_customers > 1]) / len(return_customers) * 100) if len(return_customers) > 0 else 0
            
            # Calculate peak time
            if 'Hour' in product_df.columns:
                peak_hour = int(product_df['Hour'].mode().iloc[0]) if not product_df['Hour'].mode().empty else 12
            else:
                peak_hour = 12
            
            products_list.append({
                "rank": idx + 1,
                "description": row['Description'],
                "total_revenue": float(row['total_revenue']),
                "revenue_share": round((row['total_revenue'] / filtered_df['TotalAmount'].sum()) * 100, 2) if filtered_df['TotalAmount'].sum() > 0 else 0,
                "transactions": int(row['transaction_count']),
                "transaction_share": round((row['transaction_count'] / filtered_df['InvoiceNo'].nunique()) * 100, 2) if filtered_df['InvoiceNo'].nunique() > 0 else 0,
                "customers": int(row['customer_count']),
                "avg_price": float(row['avg_price']),
                "avg_quantity": float(row['avg_quantity']),
                "records": int(row['record_count']),
                "return_customer_rate": round(float(return_customer_rate), 1),
                "peak_hour": peak_hour,
                "revenue_per_transaction": float(row['total_revenue'] / row['transaction_count']) if row['transaction_count'] > 0 else 0,
                "revenue_per_customer": float(row['total_revenue'] / row['customer_count']) if row['customer_count'] > 0 else 0
            })
        
        return jsonify({
            "success": True,
            "products": products_list,
            "metadata": {
                "total_products_analyzed": len(product_stats),
                "sort_by": sort_by,
                "filtered_records": len(filtered_df),
                "total_revenue": float(filtered_df['TotalAmount'].sum()),
                "total_transactions": filtered_df['InvoiceNo'].nunique()
            }
        })
        
    except Exception as e:
        print(f"Error in top_products: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/filters', methods=['GET'])
@cache_response(max_age=3600)
def get_filters():
    """Get available filters"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Get unique countries (sorted, limit to reasonable number)
        if 'Country' in df.columns:
            countries = sorted([str(c).strip() for c in df['Country'].dropna().unique().tolist() 
                              if c and str(c).strip() != '' and str(c).strip().lower() != 'unknown'][:30])
        else:
            countries = []
        
        # Get years present in data
        if 'Year' in df.columns:
            years = sorted([int(y) for y in df['Year'].dropna().unique().tolist()])
        else:
            years = []
        
        # Get months present in data
        if 'Month' in df.columns:
            months_present = sorted([int(m) for m in df['Month'].dropna().unique().tolist() if 1 <= m <= 12])
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_filters = [{"value": i, "name": month_names[i-1]} for i in months_present if 1 <= i <= 12]
        else:
            month_filters = []
        
        # Get hours present in data
        if 'Hour' in df.columns:
            hours_present = sorted([int(h) for h in df['Hour'].dropna().unique().tolist() if 0 <= h <= 23])
            hour_filters = [{"value": h, "name": f"{h:02d}:00"} for h in hours_present]
        else:
            hour_filters = []
        
        # Get top products for filter suggestions
        if 'Description' in df.columns:
            top_products = df['Description'].value_counts().head(50).index.tolist()
            cleaned_products = []
            seen = set()
            
            for product in top_products:
                if isinstance(product, str) and product.strip():
                    clean_product = product.strip()
                    if clean_product and clean_product not in seen:
                        seen.add(clean_product)
                        cleaned_products.append(clean_product)
            
            product_filters = sorted(cleaned_products)[:30]
        else:
            product_filters = []
        
        # Get weekdays present in data
        if 'Weekday' in df.columns:
            weekdays_present = sorted([str(w).strip() for w in df['Weekday'].dropna().unique().tolist() 
                                      if w and str(w).strip() != ''])
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekdays_sorted = sorted(weekdays_present, key=lambda x: weekday_order.index(x) if x in weekday_order else 99)
        else:
            weekdays_sorted = []
        
        filters = {
            "countries": countries,
            "years": years,
            "months": month_filters,
            "hours": hour_filters,
            "products": product_filters,
            "weekdays": weekdays_sorted,
            "statistics": {
                "total_countries": len(countries),
                "total_years": len(years),
                "total_months": len(month_filters),
                "total_products": len(product_filters),
                "data_range": {
                    "min_year": min(years) if years else None,
                    "max_year": max(years) if years else None
                }
            }
        }
        
        return jsonify({
            "success": True,
            "filters": filters,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in filters: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/product_stats', methods=['GET'])
@cache_response(max_age=300)
def get_product_stats():
    """Get detailed statistics for a specific product"""
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        product_name = request.args.get('product', '').strip()
        if not product_name:
            return jsonify({"success": False, "error": "Product name is required"}), 400
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        # Find exact or similar product
        if product_name in filtered_df['Description'].values:
            exact_match = product_name
        else:
            # Try to find similar products
            similar_products = filtered_df[filtered_df['Description'].str.contains(product_name, case=False, na=False)]['Description'].unique()
            if len(similar_products) > 0:
                exact_match = similar_products[0]
            else:
                return jsonify({
                    "success": False,
                    "error": f"Product '{product_name}' not found in filtered data"
                }), 404
        
        product_df = filtered_df[filtered_df['Description'] == exact_match]
        
        if len(product_df) == 0:
            return jsonify({
                "success": False,
                "error": f"No data found for product '{exact_match}' with current filters"
            }), 404
        
        # Calculate basic statistics
        stats = calculate_product_stats(exact_match, filtered_df)
        
        if stats is None:
            return jsonify({
                "success": False,
                "error": f"Could not calculate statistics for product '{exact_match}'"
            }), 500
        
        # Calculate trend data
        if 'Month' in product_df.columns and 'Year' in product_df.columns:
            monthly_trend = product_df.groupby(['Year', 'Month']).agg({
                'TotalAmount': 'sum',
                'Quantity': 'sum',
                'InvoiceNo': 'nunique'
            }).reset_index()
            
            monthly_trend_data = []
            for idx, row in monthly_trend.iterrows():
                monthly_trend_data.append({
                    "year": int(row['Year']),
                    "month": int(row['Month']),
                    "revenue": float(row['TotalAmount']),
                    "quantity": int(row['Quantity']),
                    "transactions": int(row['InvoiceNo'])
                })
        else:
            monthly_trend_data = []
        
        # Calculate associated products (co-purchased)
        invoices_with_product = set(product_df['InvoiceNo'].unique())
        co_purchased_products = filtered_df[filtered_df['InvoiceNo'].isin(invoices_with_product)]
        co_purchased_counts = co_purchased_products[co_purchased_products['Description'] != exact_match]['Description'].value_counts().head(10)
        
        associated_products = []
        for product, count in co_purchased_counts.items():
            co_occurrence_rate = count / len(invoices_with_product) * 100 if len(invoices_with_product) > 0 else 0
            associated_products.append({
                "product": product,
                "co_purchase_count": int(count),
                "co_occurrence_rate": round(float(co_occurrence_rate), 1)
            })
        
        # Customer segmentation
        if 'CustomerID' in product_df.columns:
            customer_stats = product_df.groupby('CustomerID').agg({
                'TotalAmount': 'sum',
                'Quantity': 'sum',
                'InvoiceNo': 'nunique'
            }).reset_index()
            
            top_customers = customer_stats.nlargest(5, 'TotalAmount')
            top_customers_list = []
            for idx, row in top_customers.iterrows():
                top_customers_list.append({
                    "customer_id": row['CustomerID'],
                    "total_spent": float(row['TotalAmount']),
                    "total_quantity": int(row['Quantity']),
                    "purchases": int(row['InvoiceNo'])
                })
        else:
            top_customers_list = []
        
        result = {
            "success": True,
            "product": {
                "name": exact_match,
                "statistics": stats,
                "monthly_trend": monthly_trend_data,
                "associated_products": associated_products,
                "top_customers": top_customers_list,
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "records_analyzed": len(product_df),
                    "time_period_covered": f"{filtered_df['Year'].min()} - {filtered_df['Year'].max()}" if 'Year' in filtered_df.columns else "Unknown"
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in product_stats: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\n🚀 Starting Intelligent Product Assortment Dashboard API...")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   Data loaded: {'Yes' if df is not None and len(df) > 0 else 'No'}")
    
    if df is not None:
        print(f"   Total records: {len(df):,}")
        print(f"   Total revenue: ${df['TotalAmount'].sum():,.2f}")
    
    print(f"\n📡 API Endpoints:")
    print(f"   http://localhost:{port}/")
    print(f"   http://localhost:{port}/api/health")
    print(f"   http://localhost:{port}/api/summary")
    print(f"   ... and more\n")
    
    app.run(debug=debug, port=port, host='0.0.0.0', threaded=True)