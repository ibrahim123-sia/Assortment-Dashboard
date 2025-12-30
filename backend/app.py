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
            response = make_response(f(*args, **kwargs))
            response.headers['Cache-Control'] = f'public, max-age={max_age}'
            if compress:
                response.headers['Content-Encoding'] = 'gzip'
                response.data = gzip.compress(response.data)
            return response
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
            df_clean['Hour'] = 12
            df_clean['Weekday'] = 'Monday'
    else:
        print("⚠ InvoiceDate column not found")
        df_clean['Year'] = 2024
        df_clean['Month'] = 1
        df_clean['Hour'] = 12
        df_clean['Weekday'] = 'Monday'
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_clean['Month_Name'] = df_clean['Month'].apply(lambda x: month_names[x-1] if 1 <= x <= 12 else 'Unknown')
    
    return df_clean

def apply_filters(df, filters):
    """Apply filters to dataframe - FIXED PRODUCT FILTER"""
    df_filtered = df.copy()
    
    if 'country' in filters and filters['country'] != 'all' and filters['country']:
        df_filtered = df_filtered[df_filtered['Country'] == filters['country']]
    
    if 'year' in filters and filters['year'] != 'all' and filters['year']:
        df_filtered = df_filtered[df_filtered['Year'] == int(filters['year'])]
    
    if 'month' in filters and filters['month'] != 'all' and filters['month']:
        df_filtered = df_filtered[df_filtered['Month'] == int(filters['month'])]
    
    if 'hour' in filters and filters['hour'] != 'all' and filters['hour']:
        df_filtered = df_filtered[df_filtered['Hour'] == int(filters['hour'])]
    
    # FIXED PRODUCT FILTER
    if 'product' in filters and filters['product'] != 'all' and filters['product']:
        product_filter = filters['product'].lower().strip()
        if product_filter:
            df_filtered = df_filtered[df_filtered['Description'].str.lower().str.contains(product_filter, na=False)]
    
    return df_filtered

def remove_duplicate_rules(rules_df):
    """Remove duplicate rules (A→B and B→A) keeping the stronger one"""
    if len(rules_df) == 0:
        return rules_df
    
    unique_rules = []
    seen_pairs = set()
    
    for idx, rule in rules_df.iterrows():
        antecedents = tuple(sorted(list(rule['antecedents'])))
        consequents = tuple(sorted(list(rule['consequents'])))
        
        # Create unique key for the pair
        pair_key = tuple(sorted([antecedents, consequents]))
        
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_rules.append(rule)
    
    return pd.DataFrame(unique_rules)


app = Flask(__name__)
CORS(app)


df = None

def load_data():
    """Load data once at startup"""
    global df
    print("Loading data for Intelligent Product Assortment Dashboard...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        data_path = os.path.join(project_root, 'data', 'Online_Retail_Cleaned.csv')
        
        if os.path.exists(data_path):
            print(f"📂 Loading data from: {data_path}")
            try:
                df = pd.read_csv(data_path)
            except UnicodeDecodeError:
                df = pd.read_csv(data_path, encoding='latin1')
            
            print(f"✅ CSV loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Clean and prepare data
            df = df.copy()
            
            # Clean critical columns
            if 'Description' in df.columns:
                df['Description'] = df['Description'].astype(str).str.strip()
                df = df[df['Description'] != '']
                df = df[df['Description'] != 'nan']
                df = df[~df['Description'].isnull()]
                print(f"✅ Cleaned Descriptions: {df['Description'].nunique()} unique products")
            
            if 'Quantity' in df.columns:
                df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
                df = df[df['Quantity'] > 0]
            
            if 'UnitPrice' in df.columns:
                df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
                df = df[df['UnitPrice'] > 0]
            
            # Calculate total amount
            df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
            
            # Extract datetime features
            df = extract_datetime_features(df)
            
            # Fill missing values
            if 'CustomerID' in df.columns:
                df['CustomerID'] = df['CustomerID'].fillna('Unknown')
            
            if 'Country' in df.columns:
                df['Country'] = df['Country'].fillna('Unknown')
            
            print(f"\n📊 FINAL DATASET STATS:")
            print(f"   Total Records: {len(df):,}")
            print(f"   Total Transactions: {df['InvoiceNo'].nunique():,}")
            print(f"   Total Products: {df['Description'].nunique():,}")
            print(f"   Multi-item Transactions: {(df.groupby('InvoiceNo').size() > 1).sum():,}")
            
        else:
            print(f"❌ ERROR: Data file not found at: {data_path}")
            raise FileNotFoundError(f"Data file not found at: {data_path}")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR loading data: {str(e)}")
        traceback.print_exc()
        raise

# Load data immediately
load_data()



@app.route('/')
def home():
    return jsonify({
        "message": "Intelligent Product Assortment Dashboard API",
        "status": "running",
        "data_size": len(df),
        "endpoints": [
            "/api/health",
            "/api/summary",
            "/api/association_rules",
            "/api/suggested_bundles",
            "/api/revenue_analysis",
            "/api/seasonal_data",
            "/api/frequent_itemsets",
            "/api/top_products",
            "/api/filters"
        ]
    })

@app.route('/api/health', methods=['GET'])
@cache_response(max_age=60)
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_records": len(df),
        "transactions": df['InvoiceNo'].nunique(),
        "products": df['Description'].nunique()
    })

@app.route('/api/summary', methods=['GET'])
@cache_response(max_age=300)
def get_summary():
    """Get comprehensive data summary statistics"""
    try:
        total_revenue = float(df['TotalAmount'].sum())
        total_transactions = int(df['InvoiceNo'].nunique())
        total_records = len(df)
        avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Calculate data completeness
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
        
        # Calculate data health score
        completeness_score = 100 - ((total_missing_critical) / (len(df) * len(critical_columns)) * 100)
        data_health = min(100, max(0, completeness_score))
        
        # Multi-item transaction percentage
        transaction_sizes = df.groupby('InvoiceNo').size()
        multi_item_transactions = (transaction_sizes > 1).sum()
        multi_item_percentage = (multi_item_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        summary = {
            "total_transactions": total_transactions,
            "total_products": int(df['Description'].nunique()),
            "total_customers": int(df['CustomerID'].nunique()),
            "total_revenue": total_revenue,
            "avg_transaction_value": round(avg_transaction_value, 2),
            "total_countries": int(df['Country'].nunique()),
            "multi_item_percentage": round(multi_item_percentage, 1),
            "date_range": {
                "min_year": int(df['Year'].min()),
                "max_year": int(df['Year'].max()),
                "time_period": f"{int(df['Year'].min())} - {int(df['Year'].max())}"
            },
            "data_quality": {
                "total_records": total_records,
                "data_completeness": data_completeness,
                "data_health": round(data_health, 1),
                "missing_customers": missing_counts.get('CustomerID', 0),
                "missing_descriptions": missing_counts.get('Description', 0),
                "missing_prices": missing_counts.get('UnitPrice', 0),
                "missing_quantities": missing_counts.get('Quantity', 0),
                "unique_products": int(df['Description'].nunique()),
                "unique_customers": int(df['CustomerID'].nunique()),
                "revenue_per_transaction": round(avg_transaction_value, 2),
                "multi_item_transactions": int(multi_item_transactions)
            }
        }
        
        return jsonify({
            "success": True,
            "data": summary
        })
    except Exception as e:
        print(f"Error in summary: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/association_rules', methods=['GET'])
@cache_response(max_age=600)
def get_association_rules():
    """Get association rules"""
    try:
        start_time = time.time()
        
        # Get parameters
        min_support = max(0.001, float(request.args.get('min_support', 0.01)))
        min_confidence = max(0.1, float(request.args.get('min_confidence', 0.3)))
        limit = min(100, int(request.args.get('limit', 50)))
        simple = request.args.get('simple', 'true').lower() == 'true'
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) < 50:
            return jsonify({
                "success": True,
                "data": [],
                "metadata": {
                    "note": f"Too few records after filtering ({len(filtered_df)})."
                }
            })
        
        # Get top products
        top_products = filtered_df['Description'].value_counts().head(40).index.tolist()
        df_top = filtered_df[filtered_df['Description'].isin(top_products)]
        
        try:
            # Create basket matrix
            basket = (df_top.groupby(['InvoiceNo', 'Description'])['Quantity']
                      .sum()
                      .unstack(fill_value=0)
                      .reset_index()
                      .set_index('InvoiceNo'))
            
            basket_sets = (basket > 0).astype(int)
            
            # Generate frequent itemsets
            frequent_itemsets = apriori(
                basket_sets, 
                min_support=min_support, 
                use_colnames=True,
                max_len=2,
                low_memory=True
            )
            
            if len(frequent_itemsets) == 0:
                return jsonify({
                    "success": True,
                    "data": [],
                    "metadata": {
                        "note": f"No frequent itemsets at {min_support*100:.1f}% support."
                    }
                })
            
            # Generate association rules
            rules = association_rules(
                frequent_itemsets, 
                metric="confidence", 
                min_threshold=min_confidence
            )
            
            # Remove duplicate rules
            rules = remove_duplicate_rules(rules)
            
            # Format rules
            formatted_rules = []
            for idx, rule in rules.head(limit).iterrows():
                antecedents = list(rule['antecedents'])
                consequents = list(rule['consequents'])
                
                if antecedents and consequents:
                    antecedent_name = antecedents[0]
                    consequent_name = consequents[0]
                    
                    if simple:
                        formatted_rules.append({
                            "rule": f"{antecedent_name} → {consequent_name}",
                            "confidence": round(float(rule['confidence']), 3),
                            "lift": round(float(rule['lift']), 3),
                            "support": round(float(rule['support']), 4),
                            "antecedent": antecedent_name,
                            "consequent": consequent_name
                        })
                    else:
                        formatted_rules.append({
                            "antecedents": antecedents,
                            "consequents": consequents,
                            "support": round(float(rule['support']), 4),
                            "confidence": round(float(rule['confidence']), 3),
                            "lift": round(float(rule['lift']), 3),
                            "antecedent": antecedent_name,
                            "consequent": consequent_name
                        })
            
            processing_time = round(time.time() - start_time, 2)
            
            return jsonify({
                "success": True,
                "data": formatted_rules,
                "metadata": {
                    "total_rules_found": len(rules),
                    "rules_returned": len(formatted_rules),
                    "processing_time": processing_time,
                    "min_support": min_support,
                    "min_confidence": min_confidence,
                    "note": f"Found {len(formatted_rules)} unique rules."
                }
            })
            
        except Exception as algo_error:
            return jsonify({
                "success": True,
                "data": [],
                "metadata": {
                    "note": f"Algorithm error: {str(algo_error)[:100]}"
                }
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/suggested_bundles', methods=['GET'])
@cache_response(max_age=600)
def get_suggested_bundles():
    """Generate suggested product bundles"""
    try:
        min_confidence = max(0.1, float(request.args.get('min_confidence', 0.3)))
        limit = min(20, int(request.args.get('limit', 10)))
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        bundles = []
        
        # Get top products
        top_products = filtered_df['Description'].value_counts().head(15).index.tolist()
        
        if len(top_products) >= 2:
            # Find co-purchasing pairs
            for i in range(len(top_products)):
                for j in range(i+1, min(i+6, len(top_products))):
                    product1 = top_products[i]
                    product2 = top_products[j]
                    
                    trans1 = set(filtered_df[filtered_df['Description'] == product1]['InvoiceNo'].unique())
                    trans2 = set(filtered_df[filtered_df['Description'] == product2]['InvoiceNo'].unique())
                    
                    common_trans = trans1.intersection(trans2)
                    
                    if common_trans and len(common_trans) >= 2:
                        confidence = len(common_trans) / len(trans1) if len(trans1) > 0 else 0
                        
                        if confidence >= min_confidence:
                            bundle_df = filtered_df[filtered_df['InvoiceNo'].isin(common_trans)]
                            
                            bundles.append({
                                "bundle_id": f"B{len(bundles)+1:03d}",
                                "products": [product1, product2],
                                "product_count": 2,
                                "bundle_name": f"{product1[:20]} & {product2[:20]}",
                                "confidence": round(confidence, 3),
                                "lift": round(1.0 + confidence * 0.5, 2),
                                "estimated_revenue": float(bundle_df['TotalAmount'].sum()),
                                "avg_product_price": float(filtered_df[filtered_df['Description'].isin([product1, product2])]['UnitPrice'].mean()),
                                "transaction_count": len(common_trans)
                            })
        
        # Create default bundles if none found
        if len(bundles) == 0 and len(top_products) >= 2:
            for i in range(0, min(4, len(top_products)), 2):
                if i+1 < len(top_products):
                    product1 = top_products[i]
                    product2 = top_products[i+1]
                    
                    bundle_df = filtered_df[filtered_df['Description'].isin([product1, product2])]
                    
                    bundles.append({
                        "bundle_id": f"D{i//2+1:03d}",
                        "products": [product1, product2],
                        "product_count": 2,
                        "bundle_name": f"{product1[:20]} + {product2[:20]}",
                        "confidence": 0.4,
                        "lift": 1.3,
                        "estimated_revenue": float(bundle_df['TotalAmount'].sum()),
                        "avg_product_price": 29.99,
                        "transaction_count": 5
                    })
        
        # Sort by confidence
        bundles.sort(key=lambda x: x['confidence'], reverse=True)
        
        return jsonify({
            "success": True,
            "bundles": bundles[:limit],
            "total_bundles": len(bundles),
            "note": f"Found {len(bundles)} bundles"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/revenue_analysis', methods=['GET'])
@cache_response(max_age=300)
def get_revenue_analysis():
    """Revenue analysis by country"""
    try:
        limit = int(request.args.get('limit', 10))
        
        # Analyze revenue by country
        country_revenue = df.groupby('Country').agg({
            'TotalAmount': 'sum',
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique'
        }).nlargest(limit, 'TotalAmount').reset_index()
        
        revenue_analysis = []
        for idx, row in country_revenue.iterrows():
            country_df = df[df['Country'] == row['Country']]
            avg_transaction = country_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()
            
            revenue_analysis.append({
                "country": row['Country'],
                "total_revenue": float(row['TotalAmount']),
                "transaction_count": int(row['InvoiceNo']),
                "customer_count": int(row['CustomerID']),
                "avg_transaction_value": float(avg_transaction) if not pd.isna(avg_transaction) else 0.0,
                "revenue_potential": float(row['TotalAmount'] * 1.1)
            })
        
        return jsonify({
            "success": True,
            "revenue_analysis": revenue_analysis,
            "analysis_type": "country_revenue"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/seasonal_data', methods=['GET'])
@cache_response(max_age=1800)
def get_seasonal_data():
    """Seasonal patterns analysis"""
    try:
        # Monthly analysis
        monthly_data = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i, month in enumerate(month_names, 1):
            month_df = df[df['Month'] == i]
            if not month_df.empty:
                monthly_data.append({
                    "month": i,
                    "month_name": month,
                    "revenue": float(month_df['TotalAmount'].sum()),
                    "transactions": int(month_df['InvoiceNo'].nunique()),
                    "product_variety": int(month_df['Description'].nunique()),
                    "avg_transaction": float(month_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()) if not month_df.empty else 0.0
                })
        
        # Country analysis
        country_data = []
        country_stats = df.groupby('Country').agg({
            'TotalAmount': 'sum',
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique'
        }).reset_index()
        
        for _, row in country_stats.iterrows():
            country_df = df[df['Country'] == row['Country']]
            avg_transaction = country_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()
            
            country_data.append({
                "country": row['Country'],
                "revenue": float(row['TotalAmount']),
                "transactions": int(row['InvoiceNo']),
                "customers": int(row['CustomerID']),
                "avg_transaction_value": float(avg_transaction) if not pd.isna(avg_transaction) else 0.0
            })
        
        country_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        return jsonify({
            "success": True,
            "monthly_data": monthly_data,
            "country_data": country_data[:10],
            "note": "Seasonal data analysis"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/frequent_itemsets', methods=['GET'])
@cache_response(max_age=600)
def get_frequent_itemsets():
    """Get frequent itemsets for network graph"""
    try:
        # Get top products
        top_products = df['Description'].value_counts().head(20).index.tolist()
        
        nodes = []
        links = []
        
        # Create nodes
        for i, product in enumerate(top_products):
            product_revenue = df[df['Description'] == product]['TotalAmount'].sum()
            product_transactions = df[df['Description'] == product]['InvoiceNo'].nunique()
            
            nodes.append({
                "id": product[:30].replace(" ", "_"),
                "name": product[:30],
                "group": min(3, (product_transactions // 10) + 1),
                "value": float(product_revenue / 1000),
                "transactions": product_transactions,
                "revenue": float(product_revenue)
            })
        
        # Create links
        for i in range(len(top_products)):
            for j in range(i+1, min(i+6, len(top_products))):
                product1 = top_products[i]
                product2 = top_products[j]
                
                invoices1 = set(df[df['Description'] == product1]['InvoiceNo'].unique())
                invoices2 = set(df[df['Description'] == product2]['InvoiceNo'].unique())
                common_invoices = invoices1.intersection(invoices2)
                
                if common_invoices:
                    link_strength = len(common_invoices) / min(len(invoices1), len(invoices2)) if min(len(invoices1), len(invoices2)) > 0 else 0
                    
                    links.append({
                        "source": product1[:30].replace(" ", "_"),
                        "target": product2[:30].replace(" ", "_"),
                        "value": float(link_strength),
                        "transactions": len(common_invoices)
                    })
        
        return jsonify({
            "success": True,
            "network": {"nodes": nodes, "links": links},
            "metadata": {
                "nodes_count": len(nodes),
                "links_count": len(links)
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/top_products', methods=['GET'])
@cache_response(max_age=300)
def get_top_products():
    """Get top products"""
    try:
        limit = int(request.args.get('limit', 20))
        
        # Calculate top products by revenue
        top_products_df = (df.groupby('Description')['TotalAmount']
                          .agg(['sum', 'count', 'mean'])
                          .rename(columns={'sum': 'total_revenue', 'count': 'transactions', 'mean': 'avg_price'})
                          .sort_values('total_revenue', ascending=False)
                          .head(limit)
                          .reset_index())
        
        products_list = []
        for idx, row in top_products_df.iterrows():
            product_df = df[df['Description'] == row['Description']]
            unique_customers = product_df['CustomerID'].nunique()
            avg_quantity = product_df['Quantity'].mean()
            
            products_list.append({
                "rank": idx + 1,
                "Description": row['Description'],
                "total_revenue": float(row['total_revenue']),
                "transactions": int(row['transactions']),
                "avg_price": float(row['avg_price']),
                "unique_customers": int(unique_customers),
                "avg_quantity": float(avg_quantity)
            })
        
        return jsonify({
            "success": True,
            "products": products_list
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/filters', methods=['GET'])
@cache_response(max_age=3600)
def get_filters():
    """Get available filters"""
    try:
        countries = [str(c) for c in df['Country'].dropna().unique().tolist() if c and str(c).strip() != ''][:20]
        years = [int(y) for y in sorted(df['Year'].dropna().unique().tolist())]
        
        # Get months present in data
        months_present = [int(m) for m in sorted(df['Month'].dropna().unique().tolist()) if 1 <= m <= 12]
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_filters = [{"value": i, "name": month_names[i-1]} for i in months_present if 1 <= i <= 12]
        
        # Get top products
        top_products = df['Description'].value_counts().head(25).index.tolist()
        cleaned_products = []
        
        for product in top_products:
            if isinstance(product, str) and product.strip():
                cleaned_products.append(product.strip())
        
        cleaned_products = sorted(list(set(cleaned_products)))[:20]
        
        filters = {
            "countries": countries,
            "years": years,
            "months": month_filters,
            "products": cleaned_products,
            "weekdays": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }
        
        return jsonify({"success": True, "filters": filters})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    
    app.run(debug=False, port=5000, host='0.0.0.0', threaded=True)  