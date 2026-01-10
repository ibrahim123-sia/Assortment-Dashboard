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
    """
    Decorator for caching and compressing API responses.
    
    Args:
        max_age: Cache duration in seconds (default: 5 minutes)
        compress: Enable gzip compression (default: True)
    
    Returns:
        Decorated function with caching and compression
    """
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
                print(f"❌ Cache decorator error: {e}")
                traceback.print_exc()
                return make_response(jsonify({
                    "success": False, 
                    "error": "Internal server error",
                    "details": str(e) if debug else None
                }), 500)
        return decorated_function
    return decorator

def extract_datetime_features(df):
    """
    Extract datetime features from the dataset for temporal analysis.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with added datetime features (Year, Month, Day, Hour, Weekday, etc.)
    """
    df_clean = df.copy()
    
    if 'InvoiceDate' in df_clean.columns:
        try:
            # Parse InvoiceDate if available
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
            # Fallback to default values
            df_clean['Year'] = 2010
            df_clean['Month'] = 1
            df_clean['Day'] = 1
            df_clean['Hour'] = 12
            df_clean['Weekday'] = 'Monday'
            df_clean['Weekday_Num'] = 0
    elif 'Year' in df_clean.columns and 'Month' in df_clean.columns:
        # Use existing datetime columns if available
        print("✓ Using existing Year, Month, Day, Hour columns")
        df_clean['Year'] = pd.to_numeric(df_clean['Year'], errors='coerce').fillna(2024).astype(int)
        df_clean['Month'] = pd.to_numeric(df_clean['Month'], errors='coerce').fillna(1).astype(int)
        df_clean['Day'] = pd.to_numeric(df_clean['Day'], errors='coerce').fillna(1) if 'Day' in df_clean.columns else 1
        df_clean['Hour'] = pd.to_numeric(df_clean['Hour'], errors='coerce').fillna(12) if 'Hour' in df_clean.columns else 12
        df_clean['Weekday'] = 'Monday'
        df_clean['Weekday_Num'] = 0
    else:
        # Create default datetime columns if none exist
        print("⚠ InvoiceDate and datetime columns not found")
        df_clean['Year'] = 2010
        df_clean['Month'] = 1
        df_clean['Day'] = 1
        df_clean['Hour'] = 12
        df_clean['Weekday'] = 'Monday'
        df_clean['Weekday_Num'] = 0
    
    # Add month names for display
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_clean['Month_Name'] = df_clean['Month'].apply(lambda x: month_names[x-1] if 1 <= x <= 12 else 'Unknown')
    
    return df_clean

def apply_filters(df, filters):
    """
    Apply multiple filters to the DataFrame with safety checks.
    
    Args:
        df: Input DataFrame
        filters: Dictionary of filter criteria
        
    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()
    
    # Debug log
    print(f"🔍 Applying filters: {filters}")
    print(f"   Initial records: {len(df_filtered):,}")
    
    # Apply country filter (with column existence check)
    if 'country' in filters and filters['country'] and filters['country'] != 'all':
        if 'Country' in df_filtered.columns:
            if filters['country'].lower() != 'unknown':
                df_filtered = df_filtered[df_filtered['Country'] == filters['country']]
                print(f"   Applied country filter: {filters['country']}")
        else:
            print(f"⚠ Country column not found, skipping country filter")
    
    # Apply year filter
    if 'year' in filters and filters['year'] and filters['year'] != 'all':
        if 'Year' in df_filtered.columns:
            try:
                year_value = int(filters['year'])
                df_filtered = df_filtered[df_filtered['Year'] == year_value]
                print(f"   Applied year filter: {year_value}")
            except ValueError:
                print(f"⚠ Invalid year value: {filters['year']}")
        else:
            print(f"⚠ Year column not found, skipping year filter")
    
    # Apply month filter
    if 'month' in filters and filters['month'] and filters['month'] != 'all':
        if 'Month' in df_filtered.columns:
            try:
                month_value = int(filters['month'])
                df_filtered = df_filtered[df_filtered['Month'] == month_value]
                print(f"   Applied month filter: {month_value}")
            except ValueError:
                print(f"⚠ Invalid month value: {filters['month']}")
        else:
            print(f"⚠ Month column not found, skipping month filter")
    
    # Apply hour filter
    if 'hour' in filters and filters['hour'] and filters['hour'] != 'all':
        if 'Hour' in df_filtered.columns:
            try:
                hour_value = int(filters['hour'])
                df_filtered = df_filtered[df_filtered['Hour'] == hour_value]
                print(f"   Applied hour filter: {hour_value}")
            except ValueError:
                print(f"⚠ Invalid hour value: {filters['hour']}")
        else:
            print(f"⚠ Hour column not found, skipping hour filter")
    
    # Apply product filter (text search in Description)
    if 'product' in filters and filters['product'] and filters['product'] != 'all':
        if 'Description' in df_filtered.columns:
            product_filter = filters['product'].lower().strip()
            if product_filter:
                # Convert to string and handle NaN values
                df_filtered['Description_clean'] = df_filtered['Description'].astype(str).str.lower()
                df_filtered = df_filtered[df_filtered['Description_clean'].str.contains(product_filter, na=False)]
                df_filtered = df_filtered.drop(columns=['Description_clean'])
                print(f"   Applied product filter: {product_filter}")
        else:
            print(f"⚠ Description column not found, skipping product filter")
    
    # Apply weekday filter
    if 'weekday' in filters and filters['weekday'] and filters['weekday'] != 'all':
        if 'Weekday' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Weekday'] == filters['weekday']]
            print(f"   Applied weekday filter: {filters['weekday']}")
        else:
            print(f"⚠ Weekday column not found, skipping weekday filter")
    
    print(f"✅ Filter application complete")
    print(f"   Records after filtering: {len(df_filtered):,}")
    print(f"   Filters applied: {filters}")
    
    return df_filtered

def remove_duplicate_rules(rules_df):
    """
    Remove duplicate association rules (A→B and B→A) keeping the one with higher confidence.
    
    Args:
        rules_df: DataFrame of association rules
        
    Returns:
        DataFrame with unique rules
    """
    if len(rules_df) == 0:
        return rules_df
    
    rules_dict = {}
    
    for idx, rule in rules_df.iterrows():
        antecedents = frozenset(rule['antecedents'])
        consequents = frozenset(rule['consequents'])
        
        # Create both possible keys (A→B and B→A)
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
    """
    Calculate detailed statistics for a specific product.
    
    Args:
        product_name: Name of the product
        df_filtered: Filtered DataFrame containing the product
        
    Returns:
        Dictionary of product statistics or None if product not found
    """
    # Find the exact product match (case-insensitive)
    product_df = df_filtered[
        df_filtered['Description'].astype(str).str.lower() == product_name.lower()
    ]
    
    if len(product_df) == 0:
        # Try partial match if exact not found
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
    
    # Calculate average price
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
    """
    Map various column name formats to standard names for compatibility.
    
    Args:
        df: Input DataFrame with potentially varying column names
        
    Returns:
        DataFrame with standardized column names
    """
    df_mapped = df.copy()
    column_mapping = {}
    
    # Map invoice-related columns
    invoice_aliases = ['Invoice', 'InvoiceNo', 'InvoiceNumber', 'TransactionID', 'TransNo']
    for col in df_mapped.columns:
        col_lower = col.lower()
        if col_lower in ['invoice', 'invoiceno', 'invoicenumber', 'transno', 'transactionid', 'transactionno']:
            if col != 'InvoiceNo':  # Only map if not already correct
                column_mapping[col] = 'InvoiceNo'
    
    # Map customer-related columns - ADDED 'customer id' (with space)
    customer_aliases = ['CustomerID', 'Customer', 'CustomerNo', 'ClientID', 'Client']
    for col in df_mapped.columns:
        col_lower = col.lower()
        if col_lower in ['customerid', 'customer', 'customerno', 'clientid', 'client', 'custid', 'customer id']:
            if col != 'CustomerID':
                column_mapping[col] = 'CustomerID'
    
    # Map price-related columns
    price_aliases = ['UnitPrice', 'Price', 'Cost', 'UnitCost']
    for col in df_mapped.columns:
        col_lower = col.lower()
        if col_lower in ['unitprice', 'price', 'cost', 'unitcost', 'sellingprice']:
            if col != 'UnitPrice':
                column_mapping[col] = 'UnitPrice'
    
    # Apply the mapping
    if column_mapping:
        df_mapped = df_mapped.rename(columns=column_mapping)
        print(f"✅ Mapped columns: {column_mapping}")
    
    return df_mapped

def validate_dataframe_columns(df, required_cols):
    """
    Validate that required columns exist in the DataFrame.
    
    Args:
        df: DataFrame to validate
        required_cols: List of required column names
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    missing_cols = [col for col in required_cols if col not in df.columns]
    return (len(missing_cols) == 0, missing_cols)

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:5000"])

# Global DataFrame to store loaded data
df = None
debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

def load_data():
    """
    Load and preprocess the retail dataset for analysis.
    Handles multiple file paths and data cleaning.
    """
    global df
    print("=" * 60)
    print("📊 Loading data for Intelligent Product Assortment Dashboard...")
    print("=" * 60)
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try multiple possible file paths
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
                print(f"📂 Found data at: {path}")
                break
        
        if not data_path:
            print(f"❌ ERROR: Data file not found at any expected location")
            print(f"   Searched paths: {possible_paths}")
            raise FileNotFoundError("Data file not found. Please ensure 'Online_Retail_II_Cleaned.csv' is available.")
        
        # Load CSV with multiple encoding attempts
        print(f"📥 Loading CSV from: {data_path}")
        for encoding in ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(data_path, encoding=encoding)
                print(f"✅ Successfully loaded with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Failed to load CSV with any encoding")
        
        print(f"✅ CSV loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
        print(f"   Columns: {list(df.columns)}")
        
        # Map column names to standard format
        df = map_column_names(df)
        
        # Display column analysis
        print(f"\n📊 COLUMN ANALYSIS:")
        for col in df.columns:
            non_null = df[col].count()
            null_count = df[col].isnull().sum()
            unique_count = df[col].nunique()
            dtype = df[col].dtype
            print(f"   {col}: {dtype}, {non_null:,} non-null, {null_count:,} null, {unique_count:,} unique")
        
        # Clean critical columns
        print(f"\n🧹 DATA CLEANING:")
        
        # Clean Description column
        if 'Description' in df.columns:
            initial_count = len(df)
            df['Description'] = df['Description'].astype(str).str.strip()
            df = df[~df['Description'].isin(['', 'nan', 'NaN', 'null', 'None'])]
            df = df[~df['Description'].isnull()]
            removed = initial_count - len(df)
            print(f"✅ Cleaned Descriptions: removed {removed:,} empty rows")
            print(f"   Unique products: {df['Description'].nunique():,}")
        else:
            print(f"❌ CRITICAL: Description column not found")
            raise ValueError("Description column is required but not found in data")
        
        # Clean Quantity column
        if 'Quantity' in df.columns:
            initial_count = len(df)
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
            df = df[df['Quantity'] > 0]
            df['Quantity'] = df['Quantity'].fillna(1).astype(int)
            removed = initial_count - len(df)
            print(f"✅ Cleaned Quantity: removed {removed:,} invalid rows")
        else:
            print(f"⚠ Warning: Quantity column not found, creating default")
            df['Quantity'] = 1
        
        # Clean Price/UnitPrice column
        if 'UnitPrice' in df.columns:
            initial_count = len(df)
            df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
            df = df[df['UnitPrice'] > 0]
            df['UnitPrice'] = df['UnitPrice'].fillna(1.0)
            removed = initial_count - len(df)
            print(f"✅ Cleaned UnitPrice: removed {removed:,} invalid rows")
        elif 'Price' in df.columns:
            df['UnitPrice'] = pd.to_numeric(df['Price'], errors='coerce')
            df['UnitPrice'] = df['UnitPrice'].fillna(1.0)
            print(f"✅ Using Price column as UnitPrice")
        else:
            print(f"⚠ Warning: No price column found, creating default")
            df['UnitPrice'] = 10.0  # Default price
        
        # Calculate TotalAmount if not present
        if 'TotalAmount' not in df.columns:
            df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
            print(f"✅ Calculated TotalAmount column")
        
        # Extract datetime features
        df = extract_datetime_features(df)
        
        # Handle missing values
        if 'CustomerID' in df.columns:
            df['CustomerID'] = df['CustomerID'].fillna('Unknown').astype(str)
            print(f"✅ Filled missing CustomerID values")
        else:
            # Create CustomerID column if it doesn't exist
            print(f"⚠ Warning: CustomerID column not found, creating default")
            df['CustomerID'] = 'Unknown'
        
        if 'Country' in df.columns:
            df['Country'] = df['Country'].fillna('Unknown').astype(str)
            print(f"✅ Filled missing Country values")
        
        # Ensure InvoiceNo exists
        if 'InvoiceNo' not in df.columns:
            invoice_cols = [col for col in df.columns if 'invoice' in col.lower()]
            if invoice_cols:
                df['InvoiceNo'] = df[invoice_cols[0]]
                print(f"✅ Using {invoice_cols[0]} as InvoiceNo")
            else:
                df['InvoiceNo'] = df.index.astype(str)
                print(f"⚠ No invoice column found, created synthetic InvoiceNo")
        
        # Ensure Month is integer type
        if 'Month' in df.columns:
            df['Month'] = pd.to_numeric(df['Month'], errors='coerce').fillna(1).astype(int)
        
        # Ensure Hour is integer type
        if 'Hour' in df.columns:
            df['Hour'] = pd.to_numeric(df['Hour'], errors='coerce').fillna(0).astype(int)
        
        # Final dataset statistics
        print(f"\n📊 FINAL DATASET STATISTICS:")
        print(f"   Total Records: {len(df):,}")
        print(f"   Total Transactions: {df['InvoiceNo'].nunique():,}")
        print(f"   Total Products: {df['Description'].nunique():,}")
        print(f"   Total Revenue: ${df['TotalAmount'].sum():,.2f}")
        print(f"   Total Customers: {df['CustomerID'].nunique():,}")
        
        if 'InvoiceNo' in df.columns:
            transaction_sizes = df.groupby('InvoiceNo').size()
            multi_item_count = (transaction_sizes > 1).sum()
            multi_item_percentage = (multi_item_count / len(transaction_sizes) * 100) if len(transaction_sizes) > 0 else 0
            print(f"   Multi-item Transactions: {multi_item_count:,} ({multi_item_percentage:.1f}%)")
        
        print(f"\n✅ DATA LOAD COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR loading data: {str(e)}")
        traceback.print_exc()
        # Create minimal valid dataframe to prevent crashes
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
        print(f"⚠ Created sample dataframe for testing ({len(df)} records)")

# Load data on startup
try:
    load_data()
except Exception as e:
    print(f"⚠ Failed to load data: {e}")
    df = pd.DataFrame()

@app.route('/')
def home():
    """Root endpoint - API information"""
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
            {"path": "/api/suggested_bundles", "method": "GET", "description": "Product bundle recommendations"},
            {"path": "/api/revenue_analysis", "method": "GET", "description": "Revenue by country analysis"},
            {"path": "/api/seasonal_data", "method": "GET", "description": "Seasonal/temporal patterns"},
            {"path": "/api/seasonal_product_analysis", "method": "GET", "description": "Seasonal analysis with product filter"},
            {"path": "/api/revenue_by_country", "method": "GET", "description": "Revenue analysis with filters"},
            {"path": "/api/product_bundles_filtered", "method": "GET", "description": "Product bundles with filters"},
            {"path": "/api/frequent_itemsets", "method": "GET", "description": "Network graph data"},
            {"path": "/api/top_products", "method": "GET", "description": "Top products ranking"},
            {"path": "/api/filters", "method": "GET", "description": "Available filter options"},
            {"path": "/api/product_stats", "method": "GET", "description": "Detailed product statistics"}
        ]
    })

@app.route('/api/health', methods=['GET'])
@cache_response(max_age=60)
def health_check():
    """Health check endpoint - verify API and data status"""
    try:
        if df is None or len(df) == 0:
            return jsonify({
                "status": "unhealthy",
                "error": "Data not loaded or empty",
                "timestamp": datetime.now().isoformat(),
                "recommendation": "Check data file and restart API"
            }), 503  # Service Unavailable
        
        # Check for critical columns
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
            "memory_usage_mb": int(df.memory_usage(deep=True).sum() / 1024 / 1024) if hasattr(df, 'memory_usage') else 0,
            "available_columns": list(df.columns),
            "data_quality": {
                "missing_descriptions": int(df['Description'].isnull().sum()) if 'Description' in df.columns else 0,
                "missing_prices": int(df['UnitPrice'].isnull().sum()) if 'UnitPrice' in df.columns else 0,
                "missing_quantities": int(df['Quantity'].isnull().sum()) if 'Quantity' in df.columns else 0
            }
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
            return jsonify({"success": False, "error": "Data not loaded or empty"}), 400
        
        # Validate required columns
        required_cols = ['InvoiceNo', 'Description', 'TotalAmount']
        is_valid, missing_cols = validate_dataframe_columns(df, required_cols)
        
        if not is_valid:
            return jsonify({
                "success": False, 
                "error": f"Missing required columns: {missing_cols}",
                "available_columns": list(df.columns)
            }), 400
        
        # Calculate basic metrics
        total_revenue = float(df['TotalAmount'].sum())
        total_transactions = int(df['InvoiceNo'].nunique())
        total_records = len(df)
        avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Calculate transaction size distribution
        multi_item_count = 0
        multi_item_percentage = 0
        if 'InvoiceNo' in df.columns:
            transaction_sizes = df.groupby('InvoiceNo').size()
            multi_item_count = (transaction_sizes > 1).sum()
            multi_item_percentage = (multi_item_count / total_transactions * 100) if total_transactions > 0 else 0
        
        # Calculate basket size statistics
        avg_basket_size = 0
        median_basket_size = 0
        if 'InvoiceNo' in df.columns and 'Quantity' in df.columns:
            basket_sizes = df.groupby('InvoiceNo')['Quantity'].sum()
            avg_basket_size = float(basket_sizes.mean()) if not basket_sizes.empty else 0
            median_basket_size = float(basket_sizes.median()) if not basket_sizes.empty else 0
        
        # Calculate product popularity
        top_10_products_percentage = 0
        if 'Description' in df.columns:
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
        
        # Time range information
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
        
        # Compile summary
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
        print(f"❌ Error in get_summary: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": "Failed to generate summary",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/association_rules', methods=['GET'])
@cache_response(max_age=600)
def get_association_rules():
    """
    Generate association rules for market basket analysis using Apriori algorithm.
    Steps:
    1. Apply filters to the dataset
    2. Create basket matrix (transactions x products)
    3. Apply Apriori algorithm to find frequent itemsets
    4. Generate association rules from frequent itemsets
    5. Filter and format rules for response
    """
    try:
        start_time = time.time()
        
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Check required columns
        required_cols = ['InvoiceNo', 'Description']
        is_valid, missing_cols = validate_dataframe_columns(df, required_cols)
        if not is_valid:
            return jsonify({
                "success": False, 
                "error": f"Missing required columns: {missing_cols}"
            }), 400
        
        # Get and validate parameters
        min_support = max(0.001, float(request.args.get('min_support', 0.01)))  # Default 1%
        min_confidence = max(0.1, float(request.args.get('min_confidence', 0.3)))  # Default 30%
        min_lift = max(0.5, float(request.args.get('min_lift', 1.0)))  # Default lift > 1
        limit = min(100, max(1, int(request.args.get('limit', 50))))  # Default 50 rules
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
        
        # Check if we have enough data after filtering
        if len(filtered_df) < 50:
            return jsonify({
                "success": True,
                "data": [],
                "metadata": {
                    "note": f"Insufficient data after filtering ({len(filtered_df)} records). Try broader filters.",
                    "minimum_recommended": 100,
                    "filtered_records": len(filtered_df),
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        # Get top products for analysis (improve performance)
        top_products = filtered_df['Description'].value_counts().head(100).index.tolist()
        df_top = filtered_df[filtered_df['Description'].isin(top_products)]
        
        if len(df_top) < 50:
            return jsonify({
                "success": True,
                "data": [],
                "metadata": {
                    "note": f"Insufficient transaction data after product filtering ({len(df_top)} records).",
                    "processing_time": round(time.time() - start_time, 2)
                }
            })
        
        try:
            # Create basket matrix (transactions x products)
            basket = (df_top.groupby(['InvoiceNo', 'Description'])['Quantity']
                      .sum()
                      .unstack(fill_value=0)
                      .reset_index()
                      .set_index('InvoiceNo'))
            
            # Convert to boolean (bought or not)
            basket_sets = (basket > 0).astype(int)
            
            # Remove infrequent products (min 3 occurrences)
            column_sums = basket_sets.sum()
            columns_to_keep = column_sums[column_sums >= 3].index.tolist()
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
            
            # Generate frequent itemsets using Apriori algorithm
            print(f"🔍 Running Apriori with min_support={min_support}")
            frequent_itemsets = apriori(
                basket_sets, 
                min_support=min_support, 
                use_colnames=True,
                max_len=2,  # Only look for pairs (for performance)
                low_memory=True,
                verbose=0
            )
            
            # If no itemsets found, try lower support
            if len(frequent_itemsets) == 0:
                adjusted_support = max(0.0005, min_support / 2)
                print(f"⚠ No itemsets found, trying lower support: {adjusted_support}")
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
                    "metadata": {
                        "note": f"No frequent itemsets found at {min_support*100:.2f}% support.",
                        "processing_time": round(time.time() - start_time, 2)
                    }
                })
            
            # Generate association rules from frequent itemsets
            rules = association_rules(
                frequent_itemsets, 
                metric="confidence", 
                min_threshold=min_confidence
            )
            
            # Filter by minimum lift
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
            
            # Sort rules by confidence and lift
            rules = rules.sort_values(['confidence', 'lift'], ascending=False)
            
            # Remove duplicate rules (A→B and B→A)
            rules = remove_duplicate_rules(rules)
            
            # Format rules for JSON response
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
            print(f"❌ Algorithm error: {algo_error}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": "Association rule generation failed",
                "details": str(algo_error) if debug else None,
                "metadata": {
                    "processing_time": round(time.time() - start_time, 2)
                }
            }), 500
            
    except Exception as e:
        print(f"❌ Error in association_rules: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": "Failed to generate association rules",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/product_bundles_filtered', methods=['GET'])
@cache_response(max_age=300)  # Reduced cache time
def get_filtered_bundles():
    """
    Optimized version with performance improvements
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Get parameters with strict limits
        min_confidence = max(0.05, min(1.0, float(request.args.get('min_confidence', 0.2))))  # Lower default
        min_transactions = max(2, int(request.args.get('min_transactions', 3)))  # Lower default
        max_products = min(30, max(10, int(request.args.get('max_products', 20))))  # Limit products analyzed
        
        # Early return for too strict filters
        if min_confidence > 0.7 and min_transactions > 10:
            return jsonify({
                "success": True,
                "bundles": [],
                "note": "Filters too strict. Try lowering min_confidence or min_transactions."
            })
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) < 100:  # Increased minimum
            return jsonify({
                "success": True,
                "bundles": [],
                "note": f"Insufficient data ({len(filtered_df)} records). Try broader filters."
            })
        
        # OPTIMIZATION: Pre-calculate product transactions
        transactions_by_product = {}
        product_counts = filtered_df['Description'].value_counts()
        top_products = product_counts.head(max_products).index.tolist()
        
        # Group by product first (much faster)
        product_groups = filtered_df.groupby('Description')
        
        for product in top_products:
            if product in product_groups.groups:
                trans_set = set(product_groups.get_group(product)['InvoiceNo'].unique())
                if len(trans_set) >= min_transactions:
                    transactions_by_product[product] = trans_set
        
        # OPTIMIZATION: Use pre-calculated total transactions
        total_transactions = filtered_df['InvoiceNo'].nunique()
        
        bundles = []
        product_list = list(transactions_by_product.keys())
        
        # OPTIMIZATION: Limit comparisons significantly
        for i in range(min(len(product_list), 20)):  # Max 20 base products
            product1 = product_list[i]
            trans1 = transactions_by_product[product1]
            
            # Limit to top 15 comparisons per product
            max_compare = min(15, len(product_list) - i - 1)
            
            for j in range(i+1, i+1 + max_compare):
                if j >= len(product_list):
                    break
                    
                product2 = product_list[j]
                trans2 = transactions_by_product[product2]
                
                # Fast intersection with length check only
                if len(trans1 & trans2) >= min_transactions:
                    common_trans = trans1.intersection(trans2)
                    confidence = len(common_trans) / min(len(trans1), len(trans2))
                    
                    if confidence >= min_confidence:
                        # Simplified metrics for speed
                        lift = (len(common_trans) * total_transactions) / (len(trans1) * len(trans2))
                        
                        bundles.append({
                            "bundle_id": f"B{len(bundles)+1:03d}",
                            "products": [product1, product2],
                            "bundle_name": f"{product1[:20]} & {product2[:20]}",
                            "confidence": round(confidence, 3),
                            "lift": round(lift, 2),
                            "transaction_count": len(common_trans),
                            "popular_products_in_bundle": []  # Skip for performance
                        })
                        
                        # Limit total bundles
                        if len(bundles) >= 50:
                            break
            
            if len(bundles) >= 50:
                break
        
        # Sort and limit
        bundles.sort(key=lambda x: (x['confidence'], x['transaction_count']), reverse=True)
        
        return jsonify({
            "success": True,
            "bundles": bundles[:20],  # Return max 20
            "total_bundles_found": len(bundles),
            "metadata": {
                "min_confidence": min_confidence,
                "min_transactions": min_transactions,
                "filtered_records": len(filtered_df),
                "products_analyzed": len(product_list),
                "filters_applied": filters,
                "execution_time_ms": 0  # You can add timing
            }
        })
        
    except Exception as e:
        print(f"Error in get_filtered_bundles: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to generate bundles. Try adjusting filters."
        }), 500

@app.route('/api/revenue_analysis', methods=['GET'])
@cache_response(max_age=300)
def get_revenue_analysis():
    """
    Analyze revenue by country with comprehensive metrics.
    This endpoint is kept for backward compatibility.
    For filtered revenue analysis, use /api/revenue_by_country.
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        
        # Check required columns
        if 'Country' not in df.columns or 'TotalAmount' not in df.columns:
            return jsonify({
                "success": False,
                "error": "Required columns (Country, TotalAmount) not found in data",
                "available_columns": list(df.columns)
            }), 400
        
        # Analyze revenue by country
        if 'CustomerID' in df.columns:
            agg_dict = {
                'TotalAmount': ['sum', 'mean', 'count'],
                'InvoiceNo': 'nunique',
                'CustomerID': 'nunique',
                'Description': 'nunique'
            }
        else:
            agg_dict = {
                'TotalAmount': ['sum', 'mean', 'count'],
                'InvoiceNo': 'nunique',
                'Description': 'nunique'
            }
        
        country_revenue = df.groupby('Country').agg(agg_dict).round(2).reset_index()
        
        # Flatten multi-index columns
        if 'CustomerID' in df.columns:
            country_revenue.columns = ['Country', 'total_revenue', 'avg_revenue', 'record_count', 
                                       'transaction_count', 'customer_count', 'product_variety']
        else:
            country_revenue.columns = ['Country', 'total_revenue', 'avg_revenue', 'record_count', 
                                       'transaction_count', 'product_variety']
            country_revenue['customer_count'] = 0
        
        # Sort by total revenue
        country_revenue = country_revenue.sort_values('total_revenue', ascending=False)
        
        revenue_analysis = []
        global_total_revenue = df['TotalAmount'].sum()
        
        for idx, row in country_revenue.head(limit).iterrows():
            country_df = df[df['Country'] == row['Country']]
            
            # Calculate additional metrics
            if 'InvoiceNo' in country_df.columns and 'TotalAmount' in country_df.columns:
                transaction_values = country_df.groupby('InvoiceNo')['TotalAmount'].sum()
                avg_transaction = transaction_values.mean() if not transaction_values.empty else 0
            else:
                avg_transaction = 0
            
            revenue_per_customer = row['total_revenue'] / row['customer_count'] if row['customer_count'] > 0 else 0
            products_per_transaction = row['product_variety'] / row['transaction_count'] if row['transaction_count'] > 0 else 0
            
            revenue_analysis.append({
                "country": str(row['Country']),
                "total_revenue": float(row['total_revenue']),
                "transaction_count": int(row['transaction_count']),
                "customer_count": int(row['customer_count']),
                "product_variety": int(row['product_variety']),
                "avg_transaction_value": float(avg_transaction),
                "revenue_per_customer": round(float(revenue_per_customer), 2),
                "products_per_transaction": round(float(products_per_transaction), 2),
                "market_share": round((row['total_revenue'] / global_total_revenue * 100), 2) if global_total_revenue > 0 else 0,
                "records": int(row['record_count'])
            })
        
        return jsonify({
            "success": True,
            "revenue_analysis": revenue_analysis,
            "analysis_type": "country_revenue",
            "metadata": {
                "total_countries_analyzed": len(country_revenue),
                "global_total_revenue": float(global_total_revenue),
                "global_avg_transaction": float(df.groupby('InvoiceNo')['TotalAmount'].sum().mean()) 
                    if 'InvoiceNo' in df.columns and 'TotalAmount' in df.columns else 0
            }
        })
        
    except Exception as e:
        print(f"❌ Error in get_revenue_analysis: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": "Failed to analyze revenue data",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/seasonal_data', methods=['GET'])
@cache_response(max_age=1800)
def get_seasonal_data():
    """
    Analyze seasonal and temporal patterns in the data.
    This endpoint is kept for backward compatibility.
    For seasonal analysis with product filter, use /api/seasonal_product_analysis.
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Check required columns
        if 'Month' not in df.columns or 'TotalAmount' not in df.columns:
            return jsonify({
                "success": False, 
                "error": "Required columns (Month, TotalAmount) not found"
            }), 400
        
        monthly_data = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Monthly analysis
        month_stats = df.groupby('Month').agg({
            'TotalAmount': ['sum', 'mean', 'count'],
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique',
            'Description': 'nunique'
        }).round(2).reset_index()
        
        # Flatten columns
        month_stats.columns = ['Month', 'total_revenue', 'avg_revenue', 'record_count', 
                               'transaction_count', 'customer_count', 'product_variety']
        
        global_total_revenue = df['TotalAmount'].sum()
        
        for idx, row in month_stats.iterrows():
            month_df = df[df['Month'] == row['Month']]
            
            # Calculate transaction-level metrics
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
        
        # Hourly analysis
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
        
        # Weekday analysis
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
            
            # Sort by weekday order
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
        
        # Find peak periods
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
        print(f"❌ Error in get_seasonal_data: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to analyze seasonal data",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/seasonal_product_analysis', methods=['GET'])
@cache_response(max_age=600)
def get_seasonal_product_analysis():
    """
    Analyze seasonal patterns for specific products with filters.
    Steps:
    1. Apply year, month, and product filters
    2. Group data by month, hour, and weekday
    3. Calculate revenue, transactions, and quantity metrics
    4. Return formatted data for frontend display
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Get parameters
        product_name = request.args.get('product', '').strip()
        year_filter = request.args.get('year', 'all')
        month_filter = request.args.get('month', 'all')
        
        # Apply basic filters first
        filtered_df = df.copy()
        
        # Apply year filter
        if year_filter != 'all' and 'Year' in filtered_df.columns:
            try:
                year_value = int(year_filter)
                filtered_df = filtered_df[filtered_df['Year'] == year_value]
            except ValueError:
                pass
        
        # Apply month filter
        if month_filter != 'all' and 'Month' in filtered_df.columns:
            try:
                month_value = int(month_filter)
                filtered_df = filtered_df[filtered_df['Month'] == month_value]
            except ValueError:
                pass
        
        # If product filter is applied, filter by product
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
                "metadata": {
                    "note": "No data found with the applied filters"
                }
            })
        
        # Ensure Month is integer type
        if 'Month' in filtered_df.columns:
            filtered_df['Month'] = pd.to_numeric(filtered_df['Month'], errors='coerce').fillna(1).astype(int)
        
        # Monthly analysis
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
        
        # Hourly analysis
        hourly_data = []
        if 'Hour' in filtered_df.columns and 'TotalAmount' in filtered_df.columns:
            # Ensure Hour is integer type
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
        
        # Weekday analysis
        weekday_data = []
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if 'Weekday' in filtered_df.columns and 'TotalAmount' in filtered_df.columns:
            weekday_stats = filtered_df.groupby('Weekday').agg({
                'TotalAmount': 'sum',
                'InvoiceNo': 'nunique',
                'Quantity': 'sum'
            }).reset_index()
            
            # Sort by weekday order
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
        
        # Find top products in filtered data
        top_products = []
        if product_name == 'all' or not product_name:
            top_products = filtered_df['Description'].value_counts().head(10).index.tolist()
        else:
            # For specific product, find related products
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
        print(f"❌ Error in get_seasonal_product_analysis: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": "Failed to analyze seasonal product data",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/revenue_by_country', methods=['GET'])
@cache_response(max_age=300)
def get_revenue_by_country():
    """
    Get revenue analysis by country with filters applied.
    Steps:
    1. Apply country and year filters
    2. Group data by country and calculate metrics
    3. Calculate market share and per-customer metrics
    4. Return sorted and limited results
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Get parameters
        limit = min(50, max(1, int(request.args.get('limit', 10))))
        country_filter = request.args.get('country', 'all')
        year_filter = request.args.get('year', 'all')
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply country filter
        if country_filter != 'all' and 'Country' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Country'] == country_filter]
        
        # Apply year filter
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
                "metadata": {
                    "note": "No data found with the applied filters"
                }
            })
        
        # Group by country
        if 'Country' in filtered_df.columns and 'TotalAmount' in filtered_df.columns:
            # Check if CustomerID exists
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
            
            # Flatten columns
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
            
            # Sort by total revenue
            country_stats = country_stats.sort_values('total_revenue', ascending=False)
            
            revenue_analysis = []
            global_total = filtered_df['TotalAmount'].sum()
            
            for idx, row in country_stats.head(limit).iterrows():
                # Calculate percentages
                market_share = (row['total_revenue'] / global_total * 100) if global_total > 0 else 0
                
                # Calculate per customer metrics
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
        print(f"❌ Error in get_revenue_by_country: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to analyze revenue by country",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/product_bundles_filtered', methods=['GET'])
@cache_response(max_age=600)
def get_product_bundles_filtered():
    """
    Get product bundles with filters applied.
    Steps:
    1. Apply country and product filters
    2. Get top products for analysis
    3. Analyze product pairs for co-purchase patterns
    4. Calculate confidence, lift, and revenue metrics
    5. Return sorted bundles
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        # Get parameters
        min_confidence = max(0.1, min(1.0, float(request.args.get('min_confidence', 0.3))))
        min_transactions = max(2, int(request.args.get('min_transactions', 5)))
        country_filter = request.args.get('country', 'all')
        product_filter = request.args.get('product', 'all')
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply country filter
        if country_filter != 'all' and 'Country' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Country'] == country_filter]
        
        if len(filtered_df) < 50:
            return jsonify({
                "success": True,
                "bundles": [],
                "metadata": {
                    "note": f"Insufficient data after filtering ({len(filtered_df)} records)",
                    "minimum_required": 50
                }
            })
        
        # Get top products for analysis
        top_products = filtered_df['Description'].value_counts().head(30).index.tolist()
        
        bundles = []
        
        # Analyze product pairs
        for i in range(len(top_products)):
            product1 = top_products[i]
            
            # If product filter is applied, only analyze bundles with that product
            if product_filter != 'all':
                if product_filter.lower() not in product1.lower():
                    continue
            
            trans1 = set(filtered_df[filtered_df['Description'] == product1]['InvoiceNo'].unique())
            
            if len(trans1) < min_transactions:
                continue
            
            for j in range(i+1, min(i+10, len(top_products))):  # Limit comparisons for performance
                product2 = top_products[j]
                
                trans2 = set(filtered_df[filtered_df['Description'] == product2]['InvoiceNo'].unique())
                
                if len(trans2) < min_transactions:
                    continue
                
                common_trans = trans1.intersection(trans2)
                
                if len(common_trans) >= min_transactions:
                    # Calculate confidence
                    confidence = len(common_trans) / len(trans1) if len(trans1) > 0 else 0
                    
                    if confidence >= min_confidence:
                        # Calculate bundle metrics
                        bundle_transactions = filtered_df[filtered_df['InvoiceNo'].isin(common_trans)]
                        bundle_revenue = bundle_transactions['TotalAmount'].sum() if 'TotalAmount' in bundle_transactions.columns else 0
                        
                        # Calculate lift
                        total_transactions = filtered_df['InvoiceNo'].nunique()
                        expected_cooccurrence = (len(trans1) * len(trans2)) / total_transactions if total_transactions > 0 else 0
                        lift = len(common_trans) / expected_cooccurrence if expected_cooccurrence > 0 else 1
                        
                        # Get bundle products
                        bundle_products = bundle_transactions['Description'].unique()
                        top_bundle_products = [
                            p for p in bundle_products 
                            if p in [product1, product2] or filtered_df[filtered_df['Description'] == p]['InvoiceNo'].nunique() >= 3
                        ][:5]
                        
                        bundles.append({
                            "bundle_id": f"B{len(bundles)+1:03d}",
                            "products": [product1, product2] + top_bundle_products[:3],
                            "main_products": [product1, product2],
                            "bundle_name": f"{product1[:20]} & {product2[:20]}",
                            "confidence": round(confidence, 3),
                            "lift": round(lift, 2),
                            "estimated_revenue": float(bundle_revenue),
                            "transaction_count": len(common_trans),
                            "unique_customers": bundle_transactions['CustomerID'].nunique() if 'CustomerID' in bundle_transactions.columns else 0
                        })
        
        # Sort bundles by confidence and transaction count
        bundles.sort(key=lambda x: (x['confidence'], x['transaction_count']), reverse=True)
        
        return jsonify({
            "success": True,
            "bundles": bundles[:20],  # Limit to 20 bundles
            "metadata": {
                "total_bundles_found": len(bundles),
                "min_confidence": min_confidence,
                "min_transactions": min_transactions,
                "filtered_records": len(filtered_df),
                "top_products_analyzed": len(top_products),
                "filters_applied": {
                    "country": country_filter,
                    "product": product_filter
                }
            }
        })
        
    except Exception as e:
        print(f"❌ Error in get_product_bundles_filtered: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to generate product bundles",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/frequent_itemsets', methods=['GET'])
@cache_response(max_age=600)
def get_frequent_itemsets():
    """
    Generate network graph data for product relationships.
    Steps:
    1. Get top products by transaction count
    2. Create nodes with product statistics
    3. Create links between products based on co-purchase patterns
    4. Calculate Jaccard similarity and lift for each link
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        min_support = max(0.001, float(request.args.get('min_support', 0.02)))
        limit = min(100, max(5, int(request.args.get('limit', 20))))
        
        # Check required columns
        if 'Description' not in df.columns:
            return jsonify({
                "success": False, 
                "error": "Description column not found"
            }), 400
        
        # Get top products
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
        
        # Create nodes (products)
        for i, product in enumerate(top_products):
            product_df = df[df['Description'] == product]
            
            # Calculate statistics
            total_revenue = product_df['TotalAmount'].sum() if 'TotalAmount' in product_df.columns else 0
            transaction_count = product_df['InvoiceNo'].nunique() if 'InvoiceNo' in product_df.columns else len(product_df)
            customer_count = product_df['CustomerID'].nunique() if 'CustomerID' in product_df.columns else 0
            
            # Categorize by price
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
            
            # Store invoices for this product
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
                "degree": 0  # Will be updated with connections
            })
        
        # Create links (relationships between products)
        link_id = 0
        for i in range(len(nodes)):
            product1 = nodes[i]['full_name']
            invoices1 = set(df[df['Description'] == product1]['InvoiceNo'].unique()) if 'InvoiceNo' in df.columns else set()
            
            for j in range(i+1, min(i+10, len(nodes))):  # Limit comparisons
                product2 = nodes[j]['full_name']
                invoices2 = set(df[df['Description'] == product2]['InvoiceNo'].unique()) if 'InvoiceNo' in df.columns else set()
                
                common_invoices = invoices1.intersection(invoices2)
                
                if common_invoices and len(common_invoices) >= 2:
                    # Calculate Jaccard similarity
                    union_invoices = invoices1.union(invoices2)
                    jaccard = len(common_invoices) / len(union_invoices) if len(union_invoices) > 0 else 0
                    
                    # Calculate lift
                    total_transactions = df['InvoiceNo'].nunique() if 'InvoiceNo' in df.columns else 1
                    expected_cooccurrence = (len(invoices1) * len(invoices2)) / total_transactions if total_transactions > 0 else 0
                    lift = len(common_invoices) / expected_cooccurrence if expected_cooccurrence > 0 else 1
                    
                    if jaccard >= 0.01:  # Minimum similarity threshold
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
        print(f"❌ Error in get_frequent_itemsets: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to generate network data",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/top_products', methods=['GET'])
@cache_response(max_age=300)
def get_top_products():
    """
    Get ranked list of top products by various metrics.
    Steps:
    1. Apply filters to the dataset
    2. Group products and calculate statistics
    3. Sort by specified metric (revenue, transactions, customers, quantity)
    4. Calculate additional metrics like return customer rate and peak hour
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        limit = min(100, max(1, int(request.args.get('limit', 20))))
        sort_by = request.args.get('sort_by', 'revenue')  # revenue, transactions, customers
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        # Check required columns
        if 'Description' not in filtered_df.columns:
            return jsonify({
                "success": False, 
                "error": "Description column not found"
            }), 400
        
        # Initialize product stats
        product_stats = filtered_df.groupby('Description').agg({
            'TotalAmount': 'sum',
            'InvoiceNo': 'nunique',
            'Quantity': 'sum'
        }).reset_index()
        
        product_stats.columns = ['Description', 'total_revenue', 'transaction_count', 'total_quantity']
        
        # Add customer count if available
        if 'CustomerID' in filtered_df.columns:
            customer_counts = filtered_df.groupby('Description')['CustomerID'].nunique().reset_index()
            customer_counts.columns = ['Description', 'customer_count']
            product_stats = pd.merge(product_stats, customer_counts, on='Description', how='left')
            product_stats['customer_count'] = product_stats['customer_count'].fillna(0).astype(int)
        else:
            product_stats['customer_count'] = 0
        
        # Add average price
        if 'UnitPrice' in filtered_df.columns:
            avg_prices = filtered_df.groupby('Description')['UnitPrice'].mean().reset_index()
            avg_prices.columns = ['Description', 'avg_price']
            product_stats = pd.merge(product_stats, avg_prices, on='Description', how='left')
            product_stats['avg_price'] = product_stats['avg_price'].fillna(0)
        else:
            product_stats['avg_price'] = 0
        
        # Add record count
        record_counts = filtered_df['Description'].value_counts().reset_index()
        record_counts.columns = ['Description', 'record_count']
        product_stats = pd.merge(product_stats, record_counts, on='Description', how='left')
        product_stats['record_count'] = product_stats['record_count'].fillna(0).astype(int)
        
        # Calculate average quantity per transaction
        product_stats['avg_quantity'] = product_stats['total_quantity'] / product_stats['transaction_count']
        product_stats['avg_quantity'] = product_stats['avg_quantity'].fillna(0)
        
        # Sort based on parameter
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
        
        # Calculate global totals for percentages
        total_filtered_revenue = filtered_df['TotalAmount'].sum() if 'TotalAmount' in filtered_df.columns else 0
        total_filtered_transactions = filtered_df['InvoiceNo'].nunique() if 'InvoiceNo' in filtered_df.columns else 0
        total_filtered_customers = filtered_df['CustomerID'].nunique() if 'CustomerID' in filtered_df.columns else 0
        
        products_list = []
        for idx, row in product_stats.head(limit).iterrows():
            # Calculate additional metrics
            product_df = filtered_df[filtered_df['Description'] == row['Description']]
            
            # Return customer rate
            return_customer_rate = 0
            if 'CustomerID' in product_df.columns and row['customer_count'] > 0:
                return_customers = product_df.groupby('CustomerID').size()
                return_customer_rate = (len(return_customers[return_customers > 1]) / row['customer_count'] * 100) if row['customer_count'] > 0 else 0
            
            # Peak hour
            peak_hour = 12
            if 'Hour' in product_df.columns:
                hour_mode = product_df['Hour'].mode()
                if not hour_mode.empty:
                    peak_hour = int(hour_mode.iloc[0])
            
            # Calculate percentages
            revenue_share = (row['total_revenue'] / total_filtered_revenue * 100) if total_filtered_revenue > 0 else 0
            transaction_share = (row['transaction_count'] / total_filtered_transactions * 100) if total_filtered_transactions > 0 else 0
            customer_share = (row['customer_count'] / total_filtered_customers * 100) if total_filtered_customers > 0 else 0
            
            # Derived metrics
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
        print(f"❌ Error in get_top_products: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": "Failed to get top products",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/filters', methods=['GET'])
@cache_response(max_age=3600)
def get_filters():
    """
    Get available filter options from the dataset.
    Steps:
    1. Extract unique values from key columns
    2. Clean and sort filter options
    3. Return organized filter data for frontend
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({
                "success": False, 
                "error": "Data not loaded",
                "note": "Please ensure data file is available and restart API"
            }), 400
        
        filters = {}
        
        # Countries
        if 'Country' in df.columns:
            countries = sorted([
                str(c).strip() for c in df['Country'].dropna().unique().tolist() 
                if c and str(c).strip() and str(c).strip().lower() != 'unknown'
            ])
            filters["countries"] = countries
        else:
            filters["countries"] = []
        
        # Years
        if 'Year' in df.columns:
            years = sorted([int(y) for y in df['Year'].dropna().unique().tolist()])
            filters["years"] = years
        else:
            filters["years"] = []
        
        # Months
        if 'Month' in df.columns:
            months_present = sorted([int(m) for m in df['Month'].dropna().unique().tolist() if 1 <= m <= 12])
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_filters = [{"value": i, "name": month_names[i-1]} for i in months_present if 1 <= i <= 12]
            filters["months"] = month_filters
        else:
            filters["months"] = []
        
        # Hours
        if 'Hour' in df.columns:
            hours_present = sorted([int(h) for h in df['Hour'].dropna().unique().tolist() if 0 <= h <= 23])
            hour_filters = [{"value": h, "name": f"{h:02d}:00"} for h in hours_present]
            filters["hours"] = hour_filters
        else:
            filters["hours"] = []
        
        # Products
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
        
        # Weekdays
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
        
        # Statistics
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
        print(f"❌ Error in get_filters: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to get filter options",
            "details": str(e) if debug else None
        }), 500

@app.route('/api/product_stats', methods=['GET'])
@cache_response(max_age=300)
def get_product_stats():
    """
    Get detailed statistics for a specific product.
    Steps:
    1. Apply filters and find the target product
    2. Calculate basic statistics and trends
    3. Find associated products (co-purchased)
    4. Identify top customers for the product
    """
    try:
        if df is None or len(df) == 0:
            return jsonify({"success": False, "error": "Data not loaded"}), 400
        
        product_name = request.args.get('product', '').strip()
        if not product_name:
            return jsonify({
                "success": False, 
                "error": "Product name is required"
            }), 400
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        if len(filtered_df) == 0:
            return jsonify({
                "success": False,
                "error": "No data available with current filters"
            }), 404
        
        # Find exact or similar product
        if product_name in filtered_df['Description'].values:
            exact_match = product_name
        else:
            # Try case-insensitive search
            similar_products = filtered_df[
                filtered_df['Description'].astype(str).str.lower().str.contains(product_name.lower(), na=False)
            ]['Description'].unique()
            
            if len(similar_products) > 0:
                exact_match = similar_products[0]
            else:
                return jsonify({
                    "success": False,
                    "error": f"Product '{product_name}' not found in filtered data",
                    "suggestion": "Try a different search term or check spelling"
                }), 404
        
        # Get product data
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
        
        # Monthly trend data
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
        
        # Associated products (co-purchased)
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
        
        # Top customers
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
        
        # Compile response
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
        print(f"❌ Error in get_product_stats: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": "Failed to get product statistics",
            "details": str(e) if debug else None
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\n{'='*60}")
    print("🚀 STARTING INTELLIGENT PRODUCT ASSORTMENT DASHBOARD API")
    print(f"{'='*60}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   Data loaded: {'Yes' if df is not None and len(df) > 0 else 'No'}")
    
    if df is not None:
        print(f"\n📊 DATA STATISTICS:")
        print(f"   Total Records: {len(df):,}")
        print(f"   Total Transactions: {df['InvoiceNo'].nunique():,}" if 'InvoiceNo' in df.columns else "   No InvoiceNo column")
        print(f"   Total Products: {df['Description'].nunique():,}" if 'Description' in df.columns else "   No Description column")
        if 'TotalAmount' in df.columns:
            print(f"   Total Revenue: ${df['TotalAmount'].sum():,.2f}")
        print(f"   Total Customers: {df['CustomerID'].nunique():,}" if 'CustomerID' in df.columns else "   No CustomerID column")
        print(f"   Available Columns: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
    
    print(f"\n📡 API ENDPOINTS:")
    print(f"   http://localhost:{port}/")
    print(f"   http://localhost:{port}/api/health")
    print(f"   http://localhost:{port}/api/summary")
    print(f"   ... and {len([r for r in app.url_map.iter_rules() if 'api' in str(r)])} more endpoints")
    print(f"\n✅ API READY")
    print(f"{'='*60}\n")
    
    app.run(debug=debug, port=port, host='0.0.0.0', threaded=True)