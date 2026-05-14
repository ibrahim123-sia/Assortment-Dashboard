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

# ==================== UTILITY FUNCTIONS ====================

def cache_response(max_age=300, compress=True):
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
                print(f"Cache decorator error: {e}")
                traceback.print_exc()
                return make_response(jsonify({
                    "success": False, 
                    "error": "Internal server error",
                    "details": str(e) if debug else None
                }), 500)
        return decorated_function
    return decorator

def extract_datetime_features(df):
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
        except Exception as e:
            print(f"Error parsing InvoiceDate: {e}")
            df_clean['Year'] = 2010
            df_clean['Month'] = 1
            df_clean['Day'] = 1
            df_clean['Hour'] = 12
            df_clean['Weekday'] = 'Monday'
            df_clean['Weekday_Num'] = 0
    elif 'Year' in df_clean.columns and 'Month' in df_clean.columns:
        df_clean['Year'] = pd.to_numeric(df_clean['Year'], errors='coerce').fillna(2024).astype(int)
        df_clean['Month'] = pd.to_numeric(df_clean['Month'], errors='coerce').fillna(1).astype(int)
        df_clean['Day'] = pd.to_numeric(df_clean['Day'], errors='coerce').fillna(1) if 'Day' in df_clean.columns else 1
        df_clean['Hour'] = pd.to_numeric(df_clean['Hour'], errors='coerce').fillna(12) if 'Hour' in df_clean.columns else 12
        df_clean['Weekday'] = 'Monday'
        df_clean['Weekday_Num'] = 0
    else:
        df_clean['Year'] = 2010
        df_clean['Month'] = 1
        df_clean['Day'] = 1
        df_clean['Hour'] = 12
        df_clean['Weekday'] = 'Monday'
        df_clean['Weekday_Num'] = 0
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_clean['Month_Name'] = df_clean['Month'].apply(lambda x: month_names[x-1] if 1 <= x <= 12 else 'Unknown')
    
    return df_clean

def apply_filters(df, filters):
    df_filtered = df.copy()
    
    if 'country' in filters and filters['country'] and filters['country'] != 'all':
        if 'Country' in df_filtered.columns:
            if filters['country'].lower() != 'unknown':
                df_filtered = df_filtered[df_filtered['Country'] == filters['country']]
        else:
            print(f"Country column not found, skipping country filter")
    
    if 'year' in filters and filters['year'] and filters['year'] != 'all':
        if 'Year' in df_filtered.columns:
            try:
                year_value = int(filters['year'])
                df_filtered = df_filtered[df_filtered['Year'] == year_value]
            except ValueError:
                print(f"Invalid year value: {filters['year']}")
        else:
            print(f"Year column not found, skipping year filter")
    
    if 'month' in filters and filters['month'] and filters['month'] != 'all':
        if 'Month' in df_filtered.columns:
            try:
                month_value = int(filters['month'])
                df_filtered = df_filtered[df_filtered['Month'] == month_value]
            except ValueError:
                print(f"Invalid month value: {filters['month']}")
        else:
            print(f"Month column not found, skipping month filter")
    
    if 'hour' in filters and filters['hour'] and filters['hour'] != 'all':
        if 'Hour' in df_filtered.columns:
            try:
                hour_value = int(filters['hour'])
                df_filtered = df_filtered[df_filtered['Hour'] == hour_value]
            except ValueError:
                print(f"Invalid hour value: {filters['hour']}")
        else:
            print(f"Hour column not found, skipping hour filter")
    
    if 'product' in filters and filters['product'] and filters['product'] != 'all':
        if 'Description' in df_filtered.columns:
            product_filter = filters['product'].lower().strip()
            if product_filter:
                df_filtered['Description_clean'] = df_filtered['Description'].astype(str).str.lower()
                df_filtered = df_filtered[df_filtered['Description_clean'].str.contains(product_filter, na=False)]
                df_filtered = df_filtered.drop(columns=['Description_clean'])
        else:
            print(f"Description column not found, skipping product filter")
    
    if 'weekday' in filters and filters['weekday'] and filters['weekday'] != 'all':
        if 'Weekday' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Weekday'] == filters['weekday']]
        else:
            print(f"Weekday column not found, skipping weekday filter")
    
    return df_filtered

def remove_duplicate_rules(rules_df):
    if len(rules_df) == 0:
        return rules_df
    
    rules_dict = {}
    
    for idx, rule in rules_df.iterrows():
        antecedents = frozenset(rule['antecedents'])
        consequents = frozenset(rule['consequents'])
        
        key1 = (antecedents, consequents)
        key2 = (consequents, antecedents)
        
        if key1 in rules_dict:
            if rule['confidence'] > rules_dict[key1]['confidence']:
                rules_dict[key1] = rule
        elif key2 in rules_dict:
            if rule['confidence'] > rules_dict[key2]['confidence']:
                rules_dict[key2] = rule
        else:
            rules_dict[key1] = rule
    
    unique_rules = pd.DataFrame(list(rules_dict.values()))
    return unique_rules

def calculate_product_stats(product_name, df_filtered):
    product_df = df_filtered[
        df_filtered['Description'].astype(str).str.lower() == product_name.lower()
    ]
    
    if len(product_df) == 0:
        product_df = df_filtered[
            df_filtered['Description'].astype(str).str.lower().str.contains(product_name.lower(), na=False)
        ]
    
    if len(product_df) == 0:
        return None
    
    stats = {
        'total_quantity': int(product_df['Quantity'].sum()) if 'Quantity' in product_df.columns else 0,
        'total_revenue': float(product_df['TotalAmount'].sum()) if 'TotalAmount' in product_df.columns else 0.0,
        'transaction_count': int(product_df['InvoiceNo'].nunique()) if 'InvoiceNo' in product_df.columns else 0,
        'customer_count': int(product_df['CustomerID'].nunique()) if 'CustomerID' in product_df.columns else 0,
        'avg_quantity_per_transaction': float(product_df.groupby('InvoiceNo')['Quantity'].sum().mean()) 
            if 'InvoiceNo' in product_df.columns and 'Quantity' in product_df.columns else 0.0,
        'peak_hour': int(product_df['Hour'].mode().iloc[0]) if 'Hour' in product_df.columns and not product_df['Hour'].mode().empty else 12,
        'most_common_weekday': str(product_df['Weekday'].mode().iloc[0]) 
            if 'Weekday' in product_df.columns and not product_df['Weekday'].mode().empty else 'Monday',
        'most_common_month': int(product_df['Month'].mode().iloc[0]) 
            if 'Month' in product_df.columns and not product_df['Month'].mode().empty else 1,
        'top_country': str(product_df['Country'].mode().iloc[0]) 
            if 'Country' in product_df.columns and not product_df['Country'].mode().empty else 'Unknown'
    }
    
    if 'UnitPrice' in product_df.columns:
        stats['avg_price'] = float(product_df['UnitPrice'].mean())
    elif 'Price' in product_df.columns:
        stats['avg_price'] = float(product_df['Price'].mean())
    elif stats['total_quantity'] > 0:
        stats['avg_price'] = stats['total_revenue'] / stats['total_quantity']
    else:
        stats['avg_price'] = 0.0
    
    return stats

def map_column_names(df):
    df_mapped = df.copy()
    column_mapping = {}
    
    for col in df_mapped.columns:
        col_lower = col.lower()
        if col_lower in ['invoice', 'invoiceno', 'invoicenumber', 'transno', 'transactionid', 'transactionno']:
            if col != 'InvoiceNo':
                column_mapping[col] = 'InvoiceNo'
    
    for col in df_mapped.columns:
        col_lower = col.lower()
        if col_lower in ['customerid', 'customer', 'customerno', 'clientid', 'client', 'custid', 'customer id']:
            if col != 'CustomerID':
                column_mapping[col] = 'CustomerID'
    
    for col in df_mapped.columns:
        col_lower = col.lower()
        if col_lower in ['unitprice', 'price', 'cost', 'unitcost', 'sellingprice']:
            if col != 'UnitPrice':
                column_mapping[col] = 'UnitPrice'
    
    if column_mapping:
        df_mapped = df_mapped.rename(columns=column_mapping)
    
    return df_mapped

def validate_dataframe_columns(df, required_cols):
    missing_cols = [col for col in required_cols if col not in df.columns]
    return (len(missing_cols) == 0, missing_cols)

# ==================== FLASK APP INITIALIZATION ====================

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:5000"])
df = None
debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# ==================== DATA LOADING FUNCTION ====================

def load_data():
    global df
    print("Loading data for Intelligent Product Assortment Dashboard...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            os.path.join(current_dir, 'data', 'Online_Retail_II_Cleaned.csv'),
            os.path.join(current_dir, 'Online_Retail_II_Cleaned.csv'),
            os.path.join(os.path.dirname(current_dir), 'data', 'Online_Retail_II_Cleaned.csv'),
            'Online_Retail_II_Cleaned.csv',
            'data/Online_Retail_II_Cleaned.csv'
        ]
        
        data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if not data_path:
            raise FileNotFoundError("Data file not found. Please ensure 'Online_Retail_II_Cleaned.csv' is available.")
        
        for encoding in ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(data_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Failed to load CSV with any encoding")
        
        df = map_column_names(df)
        
        if 'Description' in df.columns:
            initial_count = len(df)
            df['Description'] = df['Description'].astype(str).str.strip()
            df = df[~df['Description'].isin(['', 'nan', 'NaN', 'null', 'None'])]
            df = df[~df['Description'].isnull()]
        else:
            raise ValueError("Description column is required but not found in data")
        
        if 'Quantity' in df.columns:
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
            df = df[df['Quantity'] > 0]
            df['Quantity'] = df['Quantity'].fillna(1).astype(int)
        else:
            df['Quantity'] = 1
        
        if 'UnitPrice' in df.columns:
            df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
            df = df[df['UnitPrice'] > 0]
            df['UnitPrice'] = df['UnitPrice'].fillna(1.0)
        elif 'Price' in df.columns:
            df['UnitPrice'] = pd.to_numeric(df['Price'], errors='coerce')
            df['UnitPrice'] = df['UnitPrice'].fillna(1.0)
        else:
            df['UnitPrice'] = 10.0
        
        if 'TotalAmount' not in df.columns:
            df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
        
        df = extract_datetime_features(df)
        
        if 'CustomerID' in df.columns:
            df['CustomerID'] = df['CustomerID'].fillna('Unknown').astype(str)
        else:
            df['CustomerID'] = 'Unknown'
        
        if 'Country' in df.columns:
            df['Country'] = df['Country'].fillna('Unknown').astype(str)
        
        if 'InvoiceNo' not in df.columns:
            invoice_cols = [col for col in df.columns if 'invoice' in col.lower()]
            if invoice_cols:
                df['InvoiceNo'] = df[invoice_cols[0]]
            else:
                df['InvoiceNo'] = df.index.astype(str)
        
        if 'Month' in df.columns:
            df['Month'] = pd.to_numeric(df['Month'], errors='coerce').fillna(1).astype(int)
        
        if 'Hour' in df.columns:
            df['Hour'] = pd.to_numeric(df['Hour'], errors='coerce').fillna(0).astype(int)
        
        print(f"Data loaded successfully: {len(df):,} records, {df['Description'].nunique():,} products")
        
    except Exception as e:
        print(f"Error loading data: {e}")
        df = pd.DataFrame({
            'InvoiceNo': ['INV001', 'INV001', 'INV002'],
            'Description': ['Product A', 'Product B', 'Product A'],
            'Quantity': [2, 1, 3],
            'UnitPrice': [10.0, 15.0, 10.0],
            'TotalAmount': [20.0, 15.0, 30.0],
            'Country': ['UK', 'UK', 'US'],
            'CustomerID': ['C001', 'C001', 'C002'],
            'Year': [2023, 2023, 2023],
            'Month': [1, 1, 1],
            'Hour': [10, 10, 14],
            'Weekday': ['Monday', 'Monday', 'Tuesday']
        })
        print(f"Created sample dataframe for testing ({len(df)} records)")

# ==================== API ENDPOINTS ====================

# --- ROOT ENDPOINT ---
@app.route('/')
def home():
    return jsonify({
        "message": "Intelligent Product Assortment Dashboard API",
        "status": "running",
        "data_size": len(df) if df is not None else 0,
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "documentation": "See /api/health for data status",
        "endpoints": [
            {"path": "/api/health", "method": "GET", "description": "Health check and data status"},
            {"path": "/api/summary", "method": "GET", "description": "Comprehensive data summary"},
            {"path": "/api/association_rules", "method": "GET", "description": "Market basket analysis rules"},
            {"path": "/api/product_bundles_filtered", "method": "GET", "description": "Product bundle recommendations"},
            {"path": "/api/revenue_analysis", "method": "GET", "description": "Revenue by country analysis"},
            {"path": "/api/seasonal_data", "method": "GET", "description": "Seasonal/temporal patterns"},
            {"path": "/api/seasonal_product_analysis", "method": "GET", "description": "Seasonal analysis with product filter"},
            {"path": "/api/revenue_by_country", "method": "GET", "description": "Revenue analysis with filters"},
            {"path": "/api/frequent_itemsets", "method": "GET", "description": "Network graph data"},
            {"path": "/api/top_products", "method": "GET", "description": "Top products ranking"},
            {"path": "/api/filters", "method": "GET", "description": "Available filter options"},
            {"path": "/api/product_stats", "method": "GET", "description": "Detailed product statistics"}
        ]
    })

# --- HEALTH CHECK ENDPOINT ---
@app.route('/api/health', methods=['GET'])
@cache_response(max_age=60)
def health_check():
    try:
        if df is None or len(df) == 0:
            return jsonify({
                "status": "unhealthy",
                "error": "Data not loaded or empty",
                "timestamp": datetime.now().isoformat(),
                "recommendation": "Check data file and restart API"
            }), 503
        
        critical_cols = ['InvoiceNo', 'Description']
        missing_critical = [col for col in critical_cols if col not in df.columns]
        
        if missing_critical:
            return jsonify({
                "status": "degraded",
                "warning": f"Missing critical columns: {missing_critical}",
                "timestamp": datetime.now().isoformat(),
                "data_records": len(df),
                "available_columns": list(df.columns)
            }), 200
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "data_records": len(df),
            "transactions": df['InvoiceNo'].nunique() if 'InvoiceNo' in df.columns else 0,
            "products": df['Description'].nunique() if 'Description' in df.columns else 0,
            "total_revenue": float(df['TotalAmount'].sum()) if 'TotalAmount' in df.columns else 0,
            "available_columns": list(df.columns)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# --- SUMMARY ENDPOINT ---
@app.route('/api/summary', methods=['GET'])
@cache_response(max_age=300)
def get_summary():
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded or empty"}), 400
        
        required_cols = ['InvoiceNo', 'Description', 'TotalAmount']
        is_valid, missing_cols = validate_dataframe_columns(df, required_cols)
        
        if not is_valid:
            return jsonify({
                "success": False, 
                "error": f"Missing required columns: {missing_cols}",
                "available_columns": list(df.columns)
            }), 400
        
        total_revenue = float(df['TotalAmount'].sum())
        total_transactions = int(df['InvoiceNo'].nunique())
        total_records = len(df)
        avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        multi_item_count = 0
        multi_item_percentage = 0
        if 'InvoiceNo' in df.columns:
            transaction_sizes = df.groupby('InvoiceNo').size()
            multi_item_count = (transaction_sizes > 1).sum()
            multi_item_percentage = (multi_item_count / total_transactions * 100) if total_transactions > 0 else 0
        
        avg_basket_size = 0
        median_basket_size = 0
        if 'InvoiceNo' in df.columns and 'Quantity' in df.columns:
            basket_sizes = df.groupby('InvoiceNo')['Quantity'].sum()
            avg_basket_size = float(basket_sizes.mean()) if not basket_sizes.empty else 0
            median_basket_size = float(basket_sizes.median()) if not basket_sizes.empty else 0
        
        top_10_products_percentage = 0
        if 'Description' in df.columns:
            product_counts = df['Description'].value_counts()
            top_10_products_percentage = (product_counts.head(10).sum() / product_counts.sum() * 100) if product_counts.sum() > 0 else 0
        
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
        
        if 'InvoiceDate' in df.columns and df['InvoiceDate'].dtype == 'datetime64[ns]':
            min_date = df['InvoiceDate'].min()
            max_date = df['InvoiceDate'].max()
            date_range = {
                "start": min_date.strftime('%Y-%m-%d'),
                "end": max_date.strftime('%Y-%m-%d'),
                "days": (max_date - min_date).days
            }
        elif 'Year' in df.columns:
            min_year = int(df['Year'].min())
            max_year = int(df['Year'].max())
            date_range = {
                "start": f"{min_year}-01-01",
                "end": f"{max_year}-12-31",
                "years": max_year - min_year + 1
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
                "multi_item_transactions": int(multi_item_count)
            }
        }
        
        return jsonify({
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to generate summary",
            "details": str(e) if debug else None
        }), 500

# --- ASSOCIATION RULES ENDPOINT ---
@app.route('/api/association_rules', methods=['GET'])
@cache_response(max_age=600)
def get_association_rules():
    try:
        start_time = time.time()
        
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        required_cols = ['InvoiceNo', 'Description']
        is_valid, missing_cols = validate_dataframe_columns(df, required_cols)
        if not is_valid:
            return jsonify({
                "success": False, 
                "error": f"Missing required columns: {missing_cols}"
            }), 400
        
        min_support = max(0.001, float(request.args.get('min_support', 0.01)))
        min_confidence = max(0.1, float(request.args.get('min_confidence', 0.3)))
        min_lift = max(0.5, float(request.args.get('min_lift', 1.0)))
        limit = min(100, max(1, int(request.args.get('limit', 50))))
        simple = request.args.get('simple', 'true').lower() == 'true'
        
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
                "message": "Insufficient data available with the selected filters. Please try broader filters or select a different country.",
                "metadata": {
                    "filtered_records": len(filtered_df),
                    "minimum_required": 100,  
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        top_products = filtered_df['Description'].value_counts().head(100).index.tolist()
        df_top = filtered_df[filtered_df['Description'].isin(top_products)]
        
        if len(df_top) < 50:
            return jsonify({
                "success": True,
                "data": [],
                "message": "Not enough transaction data available for association analysis with current filters.",
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        try:
            basket = (df_top.groupby(['InvoiceNo', 'Description'])['Quantity']
                      .sum()
                      .unstack(fill_value=0)
                      .reset_index()
                      .set_index('InvoiceNo'))
            
            basket_sets = (basket > 0).astype(int)
            
            column_sums = basket_sets.sum()
            columns_to_keep = column_sums[column_sums >= 3].index.tolist()
            basket_sets = basket_sets[columns_to_keep]
            
            if len(basket_sets.columns) < 2:
                return jsonify({
                    "success": True,
                    "data": [],
                    "message": "No product associations found with the current filters. Try selecting a different country or broader filters.",
                    "metadata": {
                        "processing_time": round(time.time() - start_time, 2)
                    }
                })
            
            frequent_itemsets = apriori(
                basket_sets, 
                min_support=min_support, 
                use_colnames=True,
                max_len=2,
                low_memory=True,
                verbose=0
            )
            
            if len(frequent_itemsets) == 0:
                adjusted_support = max(0.0005, min_support / 2)
                frequent_itemsets = apriori(
                    basket_sets, 
                    min_support=adjusted_support, 
                    use_colnames=True,
                    max_len=2,
                    low_memory=True,
                    verbose=0
                )
                min_support = adjusted_support
            
            if len(frequent_itemsets) == 0:
                return jsonify({
                    "success": True,
                    "data": [],
                    "message": "No frequent product patterns found. The selected country may not have enough purchase data for association analysis.",
                    "metadata": {
                        "processing_time": round(time.time() - start_time, 2)
                    }
                })
            
            rules = association_rules(
                frequent_itemsets, 
                metric="confidence", 
                min_threshold=min_confidence
            )
            
            rules = rules[rules['lift'] >= min_lift]
            
            if len(rules) == 0:
                return jsonify({
                    "success": True,
                    "data": [],
                    "message": "No significant association rules found with current confidence and lift thresholds.",
                    "metadata": {
                        "processing_time": round(time.time() - start_time, 2)
                    }
                })
            
            rules = rules.sort_values(['confidence', 'lift'], ascending=False)
            rules = remove_duplicate_rules(rules)
            
            formatted_rules = []
            for idx, rule in rules.head(limit).iterrows():
                antecedents = list(rule['antecedents'])
                consequents = list(rule['consequents'])
                
                if antecedents and consequents:
                    antecedent_name = next(iter(antecedents))
                    consequent_name = next(iter(consequents))
                    
                    rule_data = {
                        "rule": f"{antecedent_name} → {consequent_name}",
                        "confidence": round(float(rule['confidence']), 3),
                        "lift": round(float(rule['lift']), 3),
                        "support": round(float(rule['support']), 4),
                        "antecedent": antecedent_name,
                        "consequent": consequent_name,
                        "antecedent_support": round(float(rule['antecedent support']), 4),
                        "consequent_support": round(float(rule['consequent support']), 4),
                        "leverage": round(float(rule['leverage']), 4),
                        "conviction": round(float(rule['conviction']), 3) if not pd.isna(rule['conviction']) else None
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
                        "min_lift": min_lift,
                        "limit": limit
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
            return jsonify({
                "success": False,
                "error": "Association rule analysis failed",
                "message": "Unable to generate association rules. The selected filters may not have sufficient data for analysis.",
                "details": str(algo_error) if debug else None,
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to generate association rules",
            "message": "An error occurred while analyzing product associations. Please try different filters.",
            "details": str(e) if debug else None
        }), 500

# --- PRODUCT BUNDLES ENDPOINT ---
@app.route('/api/product_bundles_filtered', methods=['GET'])
@cache_response(max_age=300)
def get_filtered_bundles():
    try:
        start_time = time.time()
        
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
    
        min_support = max(0.001, float(request.args.get('min_support', 0.01)))
        min_confidence = max(0.1, float(request.args.get('min_confidence', 0.3)))
        min_lift = max(0.5, float(request.args.get('min_lift', 1.0)))
        limit = min(100, max(1, int(request.args.get('limit', 50))))
        
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) < 100:
            return jsonify({
                "success": True,
                "bundles": [],
                "message": f"Not enough data available ({len(filtered_df)} records).",
                "metadata": {
                    "filtered_records": len(filtered_df),
                    "minimum_required": 100,
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
      
        top_products = filtered_df['Description'].value_counts().head(100).index.tolist()
        df_top = filtered_df[filtered_df['Description'].isin(top_products)]
        
        if len(df_top) < 50:
            return jsonify({
                "success": True,
                "bundles": [],
                "message": "Not enough transaction data for analysis.",
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
       
        basket = (df_top.groupby(['InvoiceNo', 'Description'])['Quantity']
                  .sum()
                  .unstack(fill_value=0)
                  .reset_index()
                  .set_index('InvoiceNo'))
        
        basket_sets = (basket > 0).astype(int)
        
     
        column_sums = basket_sets.sum()
        columns_to_keep = column_sums[column_sums >= 3].index.tolist()
        basket_sets = basket_sets[columns_to_keep]
        
        if len(basket_sets.columns) < 2:
            return jsonify({
                "success": True,
                "bundles": [],
                "message": "Insufficient products for bundle analysis.",
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
      
        frequent_itemsets = apriori(
            basket_sets, 
            min_support=min_support, 
            use_colnames=True,
            max_len=2,  
            low_memory=True,
            verbose=0
        )
        
        if len(frequent_itemsets) == 0:
            adjusted_support = max(0.0005, min_support / 2)
            frequent_itemsets = apriori(
                basket_sets, 
                min_support=adjusted_support, 
                use_colnames=True,
                max_len=2,
                low_memory=True,
                verbose=0
            )
            min_support = adjusted_support
        
        if len(frequent_itemsets) == 0:
            return jsonify({
                "success": True,
                "bundles": [],
                "message": "No product associations found.",
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        
        rules = association_rules(
            frequent_itemsets, 
            metric="confidence", 
            min_threshold=min_confidence
        )
        
        rules = rules[rules['lift'] >= min_lift]
        
        if len(rules) == 0:
            return jsonify({
                "success": True,
                "bundles": [],
                "message": "No strong product bundles found.",
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        rules = rules.sort_values(['confidence', 'lift'], ascending=False)
        rules = remove_duplicate_rules(rules)  
        
        
        bundles = []
        
        for idx, rule in rules.head(limit).iterrows():
            antecedents = list(rule['antecedents'])
            consequents = list(rule['consequents'])
            
            if not antecedents or not consequents:
                continue
            
            antecedent_name = next(iter(antecedents))
            consequent_name = next(iter(consequents))
            
            
            total_transactions = len(basket_sets)
            transaction_count = int(rule['support'] * total_transactions)
            
            bundles.append({
                "bundle_id": f"B{len(bundles)+1:03d}",
                "products": [antecedent_name, consequent_name],
                "bundle_name": f"{antecedent_name[:30]} & {consequent_name[:30]}",
                "confidence": round(float(rule['confidence']), 3),
                "lift": round(float(rule['lift']), 2),
                "transaction_count": transaction_count,
                "support": round(float(rule['support']), 4),
                "antecedent": antecedent_name,
                "consequent": consequent_name,
                "antecedent_support": round(float(rule['antecedent support']), 4),
                "consequent_support": round(float(rule['consequent support']), 4)
            })
        
        processing_time = round(time.time() - start_time, 2)
        
        if len(bundles) == 0:
            return jsonify({
                "success": True,
                "bundles": [],
                "message": "No product bundles found matching criteria.",
                "metadata": {
                    "processing_time": processing_time
                }
            })
        
        # Return bundles
        return jsonify({
            "success": True,
            "bundles": bundles,
            "total_bundles_found": len(bundles),
            "metadata": {
                "processing_time": processing_time,
                "parameters": {
                    "min_support": min_support,
                    "min_confidence": min_confidence,
                    "min_lift": min_lift,
                    "limit": limit
                },
                "filter_stats": {
                    "original_records": len(df),
                    "filtered_records": len(filtered_df),
                    "products_in_analysis": len(basket_sets.columns),
                    "transactions_in_analysis": len(basket_sets)
                },
                "filters_applied": filters
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to generate product bundles",
            "message": "Unable to create product bundles.",
            "details": str(e) if debug else None
        }), 500

# --- SEASONAL DATA ENDPOINT ---
@app.route('/api/seasonal_data', methods=['GET'])
@cache_response(max_age=1800)
def get_seasonal_data():
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        if 'Month' not in df.columns or 'TotalAmount' not in df.columns:
            return jsonify({
                "success": False, 
                "error": "Required columns (Month, TotalAmount) not found"
            }), 400
        
        monthly_data = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        month_stats = df.groupby('Month').agg({
            'TotalAmount': ['sum', 'mean', 'count'],
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique',
            'Description': 'nunique'
        }).round(2).reset_index()
        
        month_stats.columns = ['Month', 'total_revenue', 'avg_revenue', 'record_count', 
                               'transaction_count', 'customer_count', 'product_variety']
        
        global_total_revenue = df['TotalAmount'].sum()
        
        for idx, row in month_stats.iterrows():
            month_df = df[df['Month'] == row['Month']]
            
            if 'InvoiceNo' in month_df.columns and 'TotalAmount' in month_df.columns:
                transaction_values = month_df.groupby('InvoiceNo')['TotalAmount'].sum()
                avg_transaction = transaction_values.mean() if not transaction_values.empty else 0
                median_transaction = transaction_values.median() if not transaction_values.empty else 0
            else:
                avg_transaction = 0
                median_transaction = 0
            
            monthly_data.append({
                "month": int(row['Month']),
                "month_name": month_names[row['Month'] - 1] if 1 <= row['Month'] <= 12 else 'Unknown',
                "revenue": float(row['total_revenue']),
                "transactions": int(row['transaction_count']),
                "customers": int(row['customer_count']),
                "product_variety": int(row['product_variety']),
                "avg_transaction": float(avg_transaction),
                "median_transaction": float(median_transaction),
                "records": int(row['record_count']),
                "revenue_share": round((row['total_revenue'] / global_total_revenue * 100), 2) if global_total_revenue > 0 else 0
            })
        
        hourly_data = []
        if 'Hour' in df.columns and 'TotalAmount' in df.columns:
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
        
        weekday_data = []
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if 'Weekday' in df.columns and 'TotalAmount' in df.columns:
            weekday_stats = df.groupby('Weekday').agg({
                'TotalAmount': ['sum', 'mean', 'count'],
                'InvoiceNo': 'nunique',
                'CustomerID': 'nunique'
            }).round(2).reset_index()
            
            weekday_stats.columns = ['Weekday', 'total_revenue', 'avg_revenue', 'record_count', 
                                     'transaction_count', 'customer_count']
            
            weekday_stats['Weekday'] = pd.Categorical(weekday_stats['Weekday'], categories=weekday_order, ordered=True)
            weekday_stats = weekday_stats.sort_values('Weekday')
            
            for idx, row in weekday_stats.iterrows():
                weekday_df = df[df['Weekday'] == row['Weekday']]
                
                if 'InvoiceNo' in weekday_df.columns and 'TotalAmount' in weekday_df.columns:
                    transaction_values = weekday_df.groupby('InvoiceNo')['TotalAmount'].sum()
                    avg_transaction = transaction_values.mean() if not transaction_values.empty else 0
                else:
                    avg_transaction = 0
                
                weekday_data.append({
                    "weekday": row['Weekday'],
                    "weekday_num": weekday_order.index(row['Weekday']) if row['Weekday'] in weekday_order else 0,
                    "revenue": float(row['total_revenue']),
                    "transactions": int(row['transaction_count']),
                    "customers": int(row['customer_count']),
                    "records": int(row['record_count']),
                    "avg_transaction": float(avg_transaction),
                    "revenue_per_customer": float(row['total_revenue'] / row['customer_count']) if row['customer_count'] > 0 else 0
                })
        
        peak_month = max(monthly_data, key=lambda x: x['revenue'])['month_name'] if monthly_data else None
        peak_hour = max(hourly_data, key=lambda x: x['revenue'])['hour'] if hourly_data else None
        peak_weekday = max(weekday_data, key=lambda x: x['revenue'])['weekday'] if weekday_data else None
        
        return jsonify({
            "success": True,
            "monthly_data": monthly_data,
            "hourly_data": hourly_data,
            "weekday_data": weekday_data,
            "metadata": {
                "total_months": len(monthly_data),
                "total_hours": len(hourly_data),
                "total_weekdays": len(weekday_data),
                "peak_month": peak_month,
                "peak_hour": peak_hour,
                "peak_weekday": peak_weekday,
                "global_total_revenue": float(global_total_revenue)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to analyze seasonal data",
            "details": str(e) if debug else None
        }), 500

# --- SEASONAL PRODUCT ANALYSIS ENDPOINT ---
@app.route('/api/seasonal_product_analysis', methods=['GET'])
@cache_response(max_age=600)
def get_seasonal_product_analysis():
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        product_name = request.args.get('product', '').strip()
        year_filter = request.args.get('year', 'all')
        month_filter = request.args.get('month', 'all')
        
        filtered_df = df.copy()
        
        if year_filter != 'all' and 'Year' in filtered_df.columns:
            try:
                year_value = int(year_filter)
                filtered_df = filtered_df[filtered_df['Year'] == year_value]
            except ValueError:
                pass
        
        if month_filter != 'all' and 'Month' in filtered_df.columns:
            try:
                month_value = int(month_filter)
                filtered_df = filtered_df[filtered_df['Month'] == month_value]
            except ValueError:
                pass
        
        if product_name and product_name != 'all':
            filtered_df = filtered_df[
                filtered_df['Description'].astype(str).str.lower().str.contains(
                    product_name.lower(), na=False
                )
            ]
        
        if len(filtered_df) == 0:
            return jsonify({
                "success": True,
                "monthly_data": [],
                "hourly_data": [],
                "weekday_data": [],
                "message": "No data found with the applied filters. Try different filter combinations.",
                "metadata": {
                    "product_filter": product_name,
                    "year_filter": year_filter,
                    "month_filter": month_filter
                }
            })
        
        if 'Month' in filtered_df.columns:
            filtered_df['Month'] = pd.to_numeric(filtered_df['Month'], errors='coerce').fillna(1).astype(int)
        
        monthly_data = []
        if 'Month' in filtered_df.columns and 'TotalAmount' in filtered_df.columns:
            month_stats = filtered_df.groupby('Month').agg({
                'TotalAmount': 'sum',
                'InvoiceNo': 'nunique',
                'Description': 'nunique',
                'Quantity': 'sum'
            }).reset_index()
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            for idx, row in month_stats.iterrows():
                month_num = int(row['Month'])
                monthly_data.append({
                    "month": month_num,
                    "month_name": month_names[month_num - 1] if 1 <= month_num <= 12 else 'Unknown',
                    "revenue": float(row['TotalAmount']),
                    "transactions": int(row['InvoiceNo']),
                    "products": int(row['Description']),
                    "quantity": int(row['Quantity'])
                })
        
        hourly_data = []
        if 'Hour' in filtered_df.columns and 'TotalAmount' in filtered_df.columns:
            filtered_df['Hour'] = pd.to_numeric(filtered_df['Hour'], errors='coerce').fillna(0).astype(int)
            hour_stats = filtered_df.groupby('Hour').agg({
                'TotalAmount': 'sum',
                'InvoiceNo': 'nunique',
                'Quantity': 'sum'
            }).reset_index()
            
            for idx, row in hour_stats.iterrows():
                hour = int(row['Hour'])
                hourly_data.append({
                    "hour": hour,
                    "revenue": float(row['TotalAmount']),
                    "transactions": int(row['InvoiceNo']),
                    "quantity": int(row['Quantity']),
                    "time_period": "Morning" if 6 <= hour < 12 else 
                                  "Afternoon" if 12 <= hour < 18 else 
                                  "Evening" if 18 <= hour < 24 else "Night"
                })
        
        weekday_data = []
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if 'Weekday' in filtered_df.columns and 'TotalAmount' in filtered_df.columns:
            weekday_stats = filtered_df.groupby('Weekday').agg({
                'TotalAmount': 'sum',
                'InvoiceNo': 'nunique',
                'Quantity': 'sum'
            }).reset_index()
            
            weekday_stats['Weekday'] = pd.Categorical(
                weekday_stats['Weekday'], 
                categories=weekday_order, 
                ordered=True
            )
            weekday_stats = weekday_stats.sort_values('Weekday')
            
            for idx, row in weekday_stats.iterrows():
                weekday_data.append({
                    "weekday": str(row['Weekday']),
                    "revenue": float(row['TotalAmount']),
                    "transactions": int(row['InvoiceNo']),
                    "quantity": int(row['Quantity'])
                })
        
        top_products = []
        if product_name == 'all' or not product_name:
            top_products = filtered_df['Description'].value_counts().head(10).index.tolist()
        else:
            invoices_with_product = filtered_df[
                filtered_df['Description'].astype(str).str.lower().str.contains(
                    product_name.lower(), na=False
                )
            ]['InvoiceNo'].unique()
            
            related_products = filtered_df[
                filtered_df['InvoiceNo'].isin(invoices_with_product)
            ]['Description'].value_counts().head(10).index.tolist()
            top_products = related_products
        
        return jsonify({
            "success": True,
            "monthly_data": monthly_data,
            "hourly_data": hourly_data,
            "weekday_data": weekday_data,
            "top_products": top_products[:5],
            "metadata": {
                "total_records": len(filtered_df),
                "total_revenue": float(filtered_df['TotalAmount'].sum()) if 'TotalAmount' in filtered_df.columns else 0,
                "product_filter": product_name if product_name else 'None',
                "year_filter": year_filter,
                "month_filter": month_filter
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to analyze seasonal product data",
            "details": str(e) if debug else None
        }), 500

# --- REVENUE BY COUNTRY ENDPOINT ---
@app.route('/api/revenue_by_country', methods=['GET'])
@cache_response(max_age=300)
def get_revenue_by_country():
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        limit = min(50, max(1, int(request.args.get('limit', 10))))
        country_filter = request.args.get('country', 'all')
        year_filter = request.args.get('year', 'all')
        
        filtered_df = df.copy()
        
        if country_filter != 'all' and 'Country' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Country'] == country_filter]
        
        if year_filter != 'all' and 'Year' in filtered_df.columns:
            try:
                year_value = int(year_filter)
                filtered_df = filtered_df[filtered_df['Year'] == year_value]
            except ValueError:
                pass
        
        if len(filtered_df) == 0:
            return jsonify({
                "success": True,
                "revenue_analysis": [],
                "message": "No revenue data found for the selected country and year filters.",
                "metadata": {
                    "country_filter": country_filter,
                    "year_filter": year_filter
                }
            })
        
        if 'Country' in filtered_df.columns and 'TotalAmount' in filtered_df.columns:
            if 'CustomerID' in filtered_df.columns:
                agg_dict = {
                    'TotalAmount': ['sum', 'mean'],
                    'InvoiceNo': 'nunique',
                    'CustomerID': 'nunique',
                    'Quantity': 'sum'
                }
            else:
                agg_dict = {
                    'TotalAmount': ['sum', 'mean'],
                    'InvoiceNo': 'nunique',
                    'Quantity': 'sum'
                }
            
            country_stats = filtered_df.groupby('Country').agg(agg_dict).reset_index()
            
            if 'CustomerID' in filtered_df.columns:
                country_stats.columns = [
                    'Country', 'total_revenue', 'avg_revenue', 
                    'transaction_count', 'customer_count', 'total_quantity'
                ]
            else:
                country_stats.columns = [
                    'Country', 'total_revenue', 'avg_revenue', 
                    'transaction_count', 'total_quantity'
                ]
                country_stats['customer_count'] = 0
            
            country_stats = country_stats.sort_values('total_revenue', ascending=False)
            
            revenue_analysis = []
            global_total = filtered_df['TotalAmount'].sum()
            
            for idx, row in country_stats.head(limit).iterrows():
                market_share = (row['total_revenue'] / global_total * 100) if global_total > 0 else 0
                revenue_per_customer = row['total_revenue'] / row['customer_count'] if row['customer_count'] > 0 else 0
                avg_transaction = row['total_revenue'] / row['transaction_count'] if row['transaction_count'] > 0 else 0
                
                revenue_analysis.append({
                    "country": str(row['Country']),
                    "total_revenue": float(row['total_revenue']),
                    "transaction_count": int(row['transaction_count']),
                    "customer_count": int(row['customer_count']),
                    "total_quantity": int(row['total_quantity']),
                    "market_share": float(market_share),
                    "revenue_per_customer": float(revenue_per_customer),
                    "avg_transaction_value": float(avg_transaction),
                    "avg_revenue": float(row['avg_revenue'])
                })
            
            return jsonify({
                "success": True,
                "revenue_analysis": revenue_analysis,
                "metadata": {
                    "total_countries": len(country_stats),
                    "global_total_revenue": float(global_total),
                    "global_avg_transaction": float(filtered_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()) 
                        if 'InvoiceNo' in filtered_df.columns else 0,
                    "filters_applied": {
                        "country": country_filter,
                        "year": year_filter
                    }
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Required columns (Country, TotalAmount) not found"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to analyze revenue by country",
            "details": str(e) if debug else None
        }), 500

# --- FREQUENT ITEMSETS ENDPOINT THIS IS NETWORK GRAPH WHICH WE ARE---
@app.route('/api/frequent_itemsets', methods=['GET'])
@cache_response(max_age=600)
def get_frequent_itemsets():
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        min_support = max(0.001, float(request.args.get('min_support', 0.02)))
        limit = min(100, max(5, int(request.args.get('limit', 20))))
        
        if 'Description' not in df.columns:
            return jsonify({
                "success": False, 
                "error": "Description column not found"
            }), 400
        
        if 'TotalAmount' in df.columns and 'InvoiceNo' in df.columns:
            product_stats = df.groupby('Description').agg({
                'TotalAmount': 'sum',
                'InvoiceNo': 'nunique'
            }).reset_index()
            
            product_stats.columns = ['Description', 'total_revenue', 'transaction_count']
            top_products = product_stats.nlargest(limit, 'transaction_count')['Description'].tolist()
        else:
            top_products = df['Description'].value_counts().head(limit).index.tolist()
        
        nodes = []
        links = []
        
        for i, product in enumerate(top_products):
            product_df = df[df['Description'] == product]
            
            total_revenue = product_df['TotalAmount'].sum() if 'TotalAmount' in product_df.columns else 0
            transaction_count = product_df['InvoiceNo'].nunique() if 'InvoiceNo' in product_df.columns else len(product_df)
            customer_count = product_df['CustomerID'].nunique() if 'CustomerID' in product_df.columns else 0
            
            avg_price = 0
            if 'UnitPrice' in product_df.columns:
                avg_price = product_df['UnitPrice'].mean()
            elif 'Price' in product_df.columns:
                avg_price = product_df['Price'].mean()
            
            if avg_price < 10:
                category = "Low Price"
            elif avg_price < 50:
                category = "Medium Price"
            else:
                category = "High Price"
            
            invoices_with_product = set()
            if 'InvoiceNo' in product_df.columns:
                invoices_with_product = set(product_df['InvoiceNo'].unique())
            
            nodes.append({
                "id": f"P{i:03d}",
                "name": product[:30],
                "full_name": product,
                "group": category,
                "value": float(total_revenue / 1000) if total_revenue > 0 else 1,
                "revenue": float(total_revenue),
                "transactions": transaction_count,
                "customers": customer_count,
                "avg_price": float(avg_price) if not pd.isna(avg_price) else 0.0,
                "degree": 0
            })
        
        link_id = 0
        for i in range(len(nodes)):
            product1 = nodes[i]['full_name']
            invoices1 = set(df[df['Description'] == product1]['InvoiceNo'].unique()) if 'InvoiceNo' in df.columns else set()
            
            for j in range(i+1, min(i+10, len(nodes))):
                product2 = nodes[j]['full_name']
                invoices2 = set(df[df['Description'] == product2]['InvoiceNo'].unique()) if 'InvoiceNo' in df.columns else set()
                
                common_invoices = invoices1.intersection(invoices2)
                
                if common_invoices and len(common_invoices) >= 2:
                    union_invoices = invoices1.union(invoices2)
                    jaccard = len(common_invoices) / len(union_invoices) if len(union_invoices) > 0 else 0
                    
                    total_transactions = df['InvoiceNo'].nunique() if 'InvoiceNo' in df.columns else 1
                    expected_cooccurrence = (len(invoices1) * len(invoices2)) / total_transactions if total_transactions > 0 else 0
                    lift = len(common_invoices) / expected_cooccurrence if expected_cooccurrence > 0 else 1
                    
                    if jaccard >= 0.01:
                        common_revenue = df[df['InvoiceNo'].isin(common_invoices)]['TotalAmount'].sum() if 'TotalAmount' in df.columns else 0
                        
                        links.append({
                            "id": f"L{link_id:04d}",
                            "source": nodes[i]['id'],
                            "target": nodes[j]['id'],
                            "source_name": nodes[i]['name'],
                            "target_name": nodes[j]['name'],
                            "value": float(jaccard),
                            "transactions": len(common_invoices),
                            "strength": float(lift),
                            "revenue": float(common_revenue)
                        })
                        link_id += 1
                        
                        nodes[i]['degree'] += 1
                        nodes[j]['degree'] += 1
        
        if len(links) == 0:
            return jsonify({
                "success": True,
                "network": {
                    "nodes": nodes,
                    "links": []
                },
                "message": "No product relationships found. This may occur when products are rarely purchased together or with the current filter settings.",
                "metadata": {
                    "nodes_count": len(nodes),
                    "links_count": 0,
                    "min_support": min_support,
                    "avg_node_degree": 0,
                    "max_node_degree": 0
                }
            })
        
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
        return jsonify({
            "success": False, 
            "error": "Failed to generate network data",
            "message": "Unable to create product relationship network. Please try different filter settings.",
            "details": str(e) if debug else None
        }), 500

# --- TOP PRODUCTS ENDPOINT ---
@app.route('/api/top_products', methods=['GET'])
@cache_response(max_age=300)
def get_top_products():
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        limit = min(100, max(1, int(request.args.get('limit', 20))))
        sort_by = request.args.get('sort_by', 'revenue')
        
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) == 0:
            return jsonify({
                "success": True,
                "products": [],
                "message": "No products found with the selected filters. Try different filter combinations.",
                "metadata": {
                    "filters_applied": filters
                }
            })
        
        if 'Description' not in filtered_df.columns:
            return jsonify({
                "success": False, 
                "error": "Description column not found"
            }), 400
        
        product_stats = filtered_df.groupby('Description').agg({
            'TotalAmount': 'sum',
            'InvoiceNo': 'nunique',
            'Quantity': 'sum'
        }).reset_index()
        
        product_stats.columns = ['Description', 'total_revenue', 'transaction_count', 'total_quantity']
        
        if 'CustomerID' in filtered_df.columns:
            customer_counts = filtered_df.groupby('Description')['CustomerID'].nunique().reset_index()
            customer_counts.columns = ['Description', 'customer_count']
            product_stats = pd.merge(product_stats, customer_counts, on='Description', how='left')
            product_stats['customer_count'] = product_stats['customer_count'].fillna(0).astype(int)
        else:
            product_stats['customer_count'] = 0
        
        if 'UnitPrice' in filtered_df.columns:
            avg_prices = filtered_df.groupby('Description')['UnitPrice'].mean().reset_index()
            avg_prices.columns = ['Description', 'avg_price']
            product_stats = pd.merge(product_stats, avg_prices, on='Description', how='left')
            product_stats['avg_price'] = product_stats['avg_price'].fillna(0)
        else:
            product_stats['avg_price'] = 0
        
        record_counts = filtered_df['Description'].value_counts().reset_index()
        record_counts.columns = ['Description', 'record_count']
        product_stats = pd.merge(product_stats, record_counts, on='Description', how='left')
        product_stats['record_count'] = product_stats['record_count'].fillna(0).astype(int)
        
        product_stats['avg_quantity'] = product_stats['total_quantity'] / product_stats['transaction_count']
        product_stats['avg_quantity'] = product_stats['avg_quantity'].fillna(0)
        
        sort_column_map = {
            'revenue': 'total_revenue',
            'transactions': 'transaction_count',
            'customers': 'customer_count',
            'quantity': 'total_quantity'
        }
        
        sort_column = sort_column_map.get(sort_by, 'total_revenue')
        
        if sort_column in product_stats.columns:
            product_stats = product_stats.sort_values(sort_column, ascending=False)
        else:
            product_stats = product_stats.sort_values('total_revenue', ascending=False)
        
        total_filtered_revenue = filtered_df['TotalAmount'].sum() if 'TotalAmount' in filtered_df.columns else 0
        total_filtered_transactions = filtered_df['InvoiceNo'].nunique() if 'InvoiceNo' in filtered_df.columns else 0
        total_filtered_customers = filtered_df['CustomerID'].nunique() if 'CustomerID' in filtered_df.columns else 0
        
        products_list = []
        for idx, row in product_stats.head(limit).iterrows():
            product_df = filtered_df[filtered_df['Description'] == row['Description']]
            
            return_customer_rate = 0
            if 'CustomerID' in product_df.columns and row['customer_count'] > 0:
                return_customers = product_df.groupby('CustomerID').size()
                return_customer_rate = (len(return_customers[return_customers > 1]) / row['customer_count'] * 100) if row['customer_count'] > 0 else 0
            
            peak_hour = 12
            if 'Hour' in product_df.columns:
                hour_mode = product_df['Hour'].mode()
                if not hour_mode.empty:
                    peak_hour = int(hour_mode.iloc[0])
            
            revenue_share = (row['total_revenue'] / total_filtered_revenue * 100) if total_filtered_revenue > 0 else 0
            transaction_share = (row['transaction_count'] / total_filtered_transactions * 100) if total_filtered_transactions > 0 else 0
            customer_share = (row['customer_count'] / total_filtered_customers * 100) if total_filtered_customers > 0 else 0
            
            revenue_per_transaction = row['total_revenue'] / row['transaction_count'] if row['transaction_count'] > 0 else 0
            revenue_per_customer = row['total_revenue'] / row['customer_count'] if row['customer_count'] > 0 else 0
            
            products_list.append({
                "rank": len(products_list) + 1,
                "description": str(row['Description']),
                "total_revenue": float(row['total_revenue']),
                "revenue_share": round(revenue_share, 2),
                "transactions": int(row['transaction_count']),
                "transaction_share": round(transaction_share, 2),
                "customers": int(row['customer_count']),
                "customer_share": round(customer_share, 2),
                "avg_price": float(row['avg_price']),
                "avg_quantity": float(row['avg_quantity']),
                "total_quantity": int(row['total_quantity']),
                "records": int(row['record_count']),
                "return_customer_rate": round(float(return_customer_rate), 1),
                "peak_hour": peak_hour,
                "revenue_per_transaction": float(revenue_per_transaction),
                "revenue_per_customer": float(revenue_per_customer)
            })
        
        return jsonify({
            "success": True,
            "products": products_list,
            "metadata": {
                "total_products_analyzed": len(product_stats),
                "sort_by": sort_by,
                "filtered_records": len(filtered_df),
                "total_revenue": float(total_filtered_revenue),
                "total_transactions": total_filtered_transactions,
                "total_customers": total_filtered_customers
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to get top products",
            "details": str(e) if debug else None
        }), 500

# --- FILTERS ENDPOINT ---
@app.route('/api/filters', methods=['GET'])
@cache_response(max_age=3600)
def get_filters():
    try:
        if df is None or len(df) == 0:
            return jsonify({
                "success": False, 
                "error": "Data not loaded",
                "note": "Please ensure data file is available and restart API"
            }), 400
        
        filters = {}
        
        if 'Country' in df.columns:
            countries = sorted([
                str(c).strip() for c in df['Country'].dropna().unique().tolist() 
                if c and str(c).strip() and str(c).strip().lower() != 'unknown'
            ])
            filters["countries"] = countries
        else:
            filters["countries"] = []
        
        if 'Year' in df.columns:
            years = sorted([int(y) for y in df['Year'].dropna().unique().tolist()])
            filters["years"] = years
        else:
            filters["years"] = []
        
        if 'Month' in df.columns:
            months_present = sorted([int(m) for m in df['Month'].dropna().unique().tolist() if 1 <= m <= 12])
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_filters = [{"value": i, "name": month_names[i-1]} for i in months_present if 1 <= i <= 12]
            filters["months"] = month_filters
        else:
            filters["months"] = []
        
        if 'Hour' in df.columns:
            hours_present = sorted([int(h) for h in df['Hour'].dropna().unique().tolist() if 0 <= h <= 23])
            hour_filters = [{"value": h, "name": f"{h:02d}:00"} for h in hours_present]
            filters["hours"] = hour_filters
        else:
            filters["hours"] = []
        
        if 'Description' in df.columns:
            top_products = df['Description'].value_counts().head(100).index.tolist()
            cleaned_products = []
            seen = set()
            
            for product in top_products:
                if isinstance(product, str):
                    clean_product = product.strip()
                    if clean_product and clean_product not in seen:
                        seen.add(clean_product)
                        cleaned_products.append(clean_product)
            
            filters["products"] = sorted(cleaned_products)[:100]
        else:
            filters["products"] = []
        
        if 'Weekday' in df.columns:
            weekdays_present = sorted([
                str(w).strip() for w in df['Weekday'].dropna().unique().tolist() 
                if w and str(w).strip()
            ])
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekdays_sorted = sorted(
                weekdays_present, 
                key=lambda x: weekday_order.index(x) if x in weekday_order else 99
            )
            filters["weekdays"] = weekdays_sorted
        else:
            filters["weekdays"] = []
        
        filters["statistics"] = {
            "total_countries": len(filters["countries"]),
            "total_years": len(filters["years"]),
            "total_months": len(filters["months"]),
            "total_products": len(filters["products"]),
            "data_range": {
                "min_year": min(filters["years"]) if filters["years"] else None,
                "max_year": max(filters["years"]) if filters["years"] else None
            }
        }
        
        return jsonify({
            "success": True,
            "filters": filters,
            "timestamp": datetime.now().isoformat(),
            "data_summary": {
                "total_records": len(df),
                "total_products": df['Description'].nunique() if 'Description' in df.columns else 0,
                "total_transactions": df['InvoiceNo'].nunique() if 'InvoiceNo' in df.columns else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to get filter options",
            "details": str(e) if debug else None
        }), 500

# --- PRODUCT STATS ENDPOINT ---
@app.route('/api/product_stats', methods=['GET'])
@cache_response(max_age=300)
def get_product_stats():
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        product_name = request.args.get('product', '').strip()
        if not product_name:
            return jsonify({
                "success": False, 
                "error": "Product name is required"
            }), 400
        
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) == 0:
            return jsonify({
                "success": False,
                "error": "No data available with current filters",
                "message": "No product data found for the selected country and date filters."
            }), 404
        
        if product_name in filtered_df['Description'].values:
            exact_match = product_name
        else:
            similar_products = filtered_df[
                filtered_df['Description'].astype(str).str.lower().str.contains(product_name.lower(), na=False)
            ]['Description'].unique()
            
            if len(similar_products) > 0:
                exact_match = similar_products[0]
            else:
                return jsonify({
                    "success": False,
                    "error": f"Product '{product_name}' not found in filtered data",
                    "message": "The specified product was not found. Try a different search term or check your spelling.",
                    "suggestion": "Try a different search term or check spelling"
                }), 404
        
        product_df = filtered_df[filtered_df['Description'] == exact_match]
        
        if len(product_df) == 0:
            return jsonify({
                "success": False,
                "error": f"No data found for product '{exact_match}' with current filters",
                "message": "The product exists but has no data with the selected filters. Try broader filters."
            }), 404
        
        stats = calculate_product_stats(exact_match, filtered_df)
        
        if stats is None:
            return jsonify({
                "success": False,
                "error": f"Could not calculate statistics for product '{exact_match}'",
                "message": "Unable to calculate product statistics. Please try a different product."
            }), 500
        
        monthly_trend_data = []
        if 'Month' in product_df.columns and 'Year' in product_df.columns:
            monthly_trend = product_df.groupby(['Year', 'Month']).agg({
                'TotalAmount': 'sum',
                'Quantity': 'sum',
                'InvoiceNo': 'nunique'
            }).reset_index()
            
            for idx, row in monthly_trend.iterrows():
                monthly_trend_data.append({
                    "year": int(row['Year']),
                    "month": int(row['Month']),
                    "revenue": float(row['TotalAmount']),
                    "quantity": int(row['Quantity']),
                    "transactions": int(row['InvoiceNo'])
                })
        
        associated_products = []
        if 'InvoiceNo' in product_df.columns:
            invoices_with_product = set(product_df['InvoiceNo'].unique())
            
            if invoices_with_product and 'InvoiceNo' in filtered_df.columns:
                co_purchased_products = filtered_df[filtered_df['InvoiceNo'].isin(invoices_with_product)]
                co_purchased_counts = co_purchased_products[
                    co_purchased_products['Description'] != exact_match
                ]['Description'].value_counts().head(10)
                
                for product, count in co_purchased_counts.items():
                    co_occurrence_rate = count / len(invoices_with_product) * 100 if len(invoices_with_product) > 0 else 0
                    associated_products.append({
                        "product": product,
                        "co_purchase_count": int(count),
                        "co_occurrence_rate": round(float(co_occurrence_rate), 1)
                    })
        
        top_customers_list = []
        if 'CustomerID' in product_df.columns:
            customer_stats = product_df.groupby('CustomerID').agg({
                'TotalAmount': 'sum',
                'Quantity': 'sum',
                'InvoiceNo': 'nunique'
            }).reset_index()
            
            top_customers = customer_stats.nlargest(5, 'TotalAmount')
            for idx, row in top_customers.iterrows():
                top_customers_list.append({
                    "customer_id": row['CustomerID'],
                    "total_spent": float(row['TotalAmount']),
                    "total_quantity": int(row['Quantity']),
                    "purchases": int(row['InvoiceNo'])
                })
        
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
                    "time_period_covered": f"{filtered_df['Year'].min()} - {filtered_df['Year'].max()}" 
                        if 'Year' in filtered_df.columns else "Unknown",
                    "filters_applied": filters
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": "Failed to get product statistics",
            "message": "An error occurred while retrieving product statistics. Please try again.",
            "details": str(e) if debug else None
        }), 500

# ==================== MAIN EXECUTION ====================

if __name__ == '__main__':
    load_data()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\nIntelligent Product Assortment Dashboard API")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Data loaded: {'Yes' if df is not None and len(df) > 0 else 'No'}")
    
    if df is not None:
        print(f"Total Records: {len(df):,}")
        print(f"Total Transactions: {df['InvoiceNo'].nunique():,}" if 'InvoiceNo' in df.columns else "No InvoiceNo column")
        print(f"Total Products: {df['Description'].nunique():,}" if 'Description' in df.columns else "No Description column")
        if 'TotalAmount' in df.columns:
            print(f"Total Revenue: ${df['TotalAmount'].sum():,.2f}")
    
    print(f"\nAPI Ready at http://localhost:{port}")
    
    app.run(debug=debug, port=port, host='0.0.0.0', threaded=True)