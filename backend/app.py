"""
Intelligent Product Assortment Dashboard using Market Basket Analysis
Backend API Implementation - ACTUAL DATA VERSION WITH PRODUCT FILTERS
"""

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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
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
    
    # Check for date columns
    date_columns = [col for col in df_clean.columns if 'date' in col.lower() or 'time' in col.lower()]
    
    if date_columns:
        date_col = date_columns[0]
        print(f"✓ Found date column: {date_col}")
        
        try:
            # Convert to datetime
            df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
            
            # Extract date components
            df_clean['Year'] = df_clean[date_col].dt.year
            df_clean['Month'] = df_clean[date_col].dt.month
            df_clean['Day'] = df_clean[date_col].dt.day
            df_clean['Hour'] = df_clean[date_col].dt.hour
            df_clean['Weekday'] = df_clean[date_col].dt.day_name()
            df_clean['Weekday_Num'] = df_clean[date_col].dt.dayofweek
        except Exception as e:
            print(f"⚠ Error parsing dates: {e}")
    
    # Ensure required columns exist with actual data if possible
    if 'Year' not in df_clean.columns or df_clean['Year'].isna().all():
        df_clean['Year'] = 2024
    
    if 'Month' not in df_clean.columns or df_clean['Month'].isna().all():
        df_clean['Month'] = 1
    
    if 'Hour' not in df_clean.columns or df_clean['Hour'].isna().all():
        df_clean['Hour'] = 12
    
    if 'Weekday' not in df_clean.columns or df_clean['Weekday'].isna().all():
        df_clean['Weekday'] = 'Monday'
    
    # Create month names
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_clean['Month_Name'] = df_clean['Month'].apply(lambda x: month_names[x-1] if 1 <= x <= 12 else 'Unknown')
    
    return df_clean

def apply_filters(df, filters):
    """Apply filters to dataframe"""
    df_filtered = df.copy()
    
    # Apply country filter
    if 'country' in filters and filters['country'] != 'all':
        df_filtered = df_filtered[df_filtered['Country'] == filters['country']]
    
    # Apply year filter
    if 'year' in filters and filters['year'] != 'all':
        df_filtered = df_filtered[df_filtered['Year'] == int(filters['year'])]
    
    # Apply month filter
    if 'month' in filters and filters['month'] != 'all':
        df_filtered = df_filtered[df_filtered['Month'] == int(filters['month'])]
    
    # Apply hour filter
    if 'hour' in filters and filters['hour'] != 'all':
        df_filtered = df_filtered[df_filtered['Hour'] == int(filters['hour'])]
    
    # Apply product filter
    if 'product' in filters and filters['product'] != 'all':
        product = filters['product'].lower()
        df_filtered = df_filtered[df_filtered['Description'].str.lower().str.contains(product, na=False)]
    
    return df_filtered

# ============================================================================
# INITIALIZE FLASK APP
# ============================================================================
app = Flask(__name__)
CORS(app)

# ============================================================================
# DATA LOADING - ACTUAL DATA ONLY
# ============================================================================
print("Loading data for Intelligent Product Assortment Dashboard...")

# Load actual data
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_path = os.path.join(project_root, 'data', 'Online_Retail_Cleaned.csv')
    
    if os.path.exists(data_path):
        try:
            df = pd.read_csv(data_path)
        except UnicodeDecodeError:
            df = pd.read_csv(data_path, encoding='latin1')
        
        print(f"✓ CSV data loaded successfully! Shape: {df.shape}")
        
        # Clean and prepare data
        df = df.copy()
        
        # Ensure required columns exist
        required_columns = ['InvoiceNo', 'Description', 'Quantity', 'UnitPrice', 'CustomerID', 'Country']
        for col in required_columns:
            if col not in df.columns:
                print(f"⚠ Missing column: {col}")
                if col == 'Description':
                    df['Description'] = 'Product_' + df.index.astype(str)
                elif col == 'Country':
                    df['Country'] = 'Unknown'
                elif col == 'CustomerID':
                    df['CustomerID'] = 'Unknown'
                elif col == 'UnitPrice':
                    df['UnitPrice'] = 10.0
                elif col == 'Quantity':
                    df['Quantity'] = 1
        
        # Calculate total amount
        df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
        
        # Extract datetime features
        df = extract_datetime_features(df)
        
        # Clean product descriptions
        df['Description'] = df['Description'].astype(str).str.strip()
        
    else:
        print("❌ ERROR: Data file not found!")
        raise FileNotFoundError("Data file not found at: " + data_path)
        
except Exception as e:
    print(f"❌ CRITICAL ERROR loading data: {str(e)}")
    raise

print(f"\n📊 ACTUAL DATA SUMMARY:")
print(f"Total Records: {len(df):,}")
print(f"Total Transactions: {df['InvoiceNo'].nunique():,}")
print(f"Total Products: {df['Description'].nunique():,}")
print(f"Total Customers: {df['CustomerID'].nunique():,}")
print(f"Total Revenue: ${df['TotalAmount'].sum():,.2f}")
print(f"Date Range: {df['Year'].min()}-{df['Year'].max()}")
print(f"Countries: {df['Country'].nunique()}")

# ============================================================================
# API ENDPOINTS
# ============================================================================

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
        "data_records": len(df)
    })

@app.route('/api/summary', methods=['GET'])
@cache_response(max_age=300)
def get_summary():
    """Get comprehensive data summary statistics"""
    try:
        total_revenue = float(df['TotalAmount'].sum())
        total_transactions = int(df['InvoiceNo'].nunique())
        avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        summary = {
            "total_transactions": total_transactions,
            "total_products": int(df['Description'].nunique()),
            "total_customers": int(df['CustomerID'].nunique()),
            "total_revenue": total_revenue,
            "avg_transaction_value": avg_transaction_value,
            "total_countries": int(df['Country'].nunique()),
            "date_range": {
                "min_year": int(df['Year'].min()),
                "max_year": int(df['Year'].max()),
                "time_period": f"{int(df['Year'].min())} - {int(df['Year'].max())}"
            }
        }
        
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/association_rules', methods=['GET'])
@cache_response(max_age=600)
def get_association_rules():
    """Get association rules with filters"""
    try:
        # Get parameters
        min_support = float(request.args.get('min_support', 0.01))
        min_confidence = float(request.args.get('min_confidence', 0.3))
        limit = int(request.args.get('limit', 100))
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
                    "total_rules_found": 0,
                    "rules_returned": 0,
                    "filtered_records": len(filtered_df),
                    "note": "Insufficient data for association rule mining after filtering"
                }
            })
        
        try:
            # Create basket data
            basket = (filtered_df.groupby(['InvoiceNo', 'Description'])['Quantity']
                      .sum()
                      .unstack(fill_value=0)
                      .reset_index()
                      .set_index('InvoiceNo'))
            
            # Convert to binary
            basket_sets = (basket > 0).astype(int)
            
            # Generate frequent itemsets
            frequent_itemsets = apriori(basket_sets, 
                                       min_support=min_support, 
                                       use_colnames=True,
                                       max_len=3)
            
            if len(frequent_itemsets) == 0:
                return jsonify({
                    "success": True,
                    "data": [],
                    "metadata": {
                        "total_rules_found": 0,
                        "rules_returned": 0,
                        "filtered_records": len(filtered_df),
                        "note": "No frequent itemsets found at current support threshold"
                    }
                })
            
            # Generate association rules
            rules = association_rules(frequent_itemsets, 
                                     metric="confidence", 
                                     min_threshold=min_confidence)
            
            # Format rules
            formatted_rules = []
            for _, rule in rules.head(limit).iterrows():
                antecedents = list(rule['antecedents'])
                consequents = list(rule['consequents'])
                
                if not antecedents or not consequents:
                    continue
                
                if simple:
                    formatted_rules.append({
                        "rule": f"{antecedents[0][:50]} → {consequents[0][:50]}",
                        "confidence": round(float(rule['confidence']), 3),
                        "lift": round(float(rule['lift']), 3),
                        "support": round(float(rule['support']), 4)
                    })
                else:
                    formatted_rules.append({
                        "antecedents": antecedents,
                        "consequents": consequents,
                        "support": float(rule['support']),
                        "confidence": float(rule['confidence']),
                        "lift": float(rule['lift'])
                    })
            
            return jsonify({
                "success": True,
                "data": formatted_rules,
                "metadata": {
                    "total_rules_found": len(rules),
                    "rules_returned": len(formatted_rules),
                    "filtered_records": len(filtered_df),
                    "min_support": min_support,
                    "min_confidence": min_confidence,
                    "filters_applied": filters
                }
            })
            
        except Exception as algo_error:
            return jsonify({
                "success": True,
                "data": [],
                "metadata": {
                    "total_rules_found": 0,
                    "rules_returned": 0,
                    "error": str(algo_error)
                }
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/suggested_bundles', methods=['GET'])
@cache_response(max_age=600)
def get_suggested_bundles():
    """Generate suggested product bundles"""
    try:
        min_confidence = float(request.args.get('min_confidence', 0.3))
        limit = int(request.args.get('limit', 10))
        
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
        
        if len(filtered_df) >= 100:
            try:
                # Create basket data
                basket = (filtered_df.groupby(['InvoiceNo', 'Description'])['Quantity']
                          .sum()
                          .unstack(fill_value=0)
                          .reset_index()
                          .set_index('InvoiceNo'))
                
                basket_sets = (basket > 0).astype(int)
                
                # Find frequent itemsets
                frequent_itemsets = apriori(basket_sets, 
                                           min_support=0.02, 
                                           use_colnames=True,
                                           max_len=3)
                
                for idx, itemset in frequent_itemsets.head(limit).iterrows():
                    items = list(itemset['itemsets'])
                    if len(items) >= 2:
                        bundle_df = filtered_df[filtered_df['Description'].isin(items)]
                        
                        if not bundle_df.empty:
                            transactions_with_items = bundle_df.groupby('InvoiceNo').filter(
                                lambda x: len(x['Description'].unique()) >= 2
                            )['InvoiceNo'].nunique()
                            
                            total_transactions = filtered_df['InvoiceNo'].nunique()
                            support = transactions_with_items / total_transactions if total_transactions > 0 else 0
                            
                            if support >= min_confidence:
                                bundles.append({
                                    "bundle_id": f"B{idx:03d}",
                                    "products": items,
                                    "product_count": len(items),
                                    "bundle_name": f"Bundle {idx}",
                                    "confidence": round(support, 3),
                                    "estimated_revenue": float(bundle_df['TotalAmount'].sum()),
                                    "avg_product_price": float(bundle_df['UnitPrice'].mean()) if not bundle_df.empty else 0.0,
                                    "transaction_count": transactions_with_items
                                })
            except Exception as e:
                print(f"Bundle generation error: {e}")
        
        return jsonify({
            "success": True,
            "bundles": bundles[:limit],
            "total_bundles": len(bundles),
            "filters_applied": filters
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/revenue_analysis', methods=['GET'])
@cache_response(max_age=300)
def get_revenue_analysis():
    """Revenue analysis by country"""
    try:
        limit = int(request.args.get('limit', 10))
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        revenue_analysis = []
        
        # Analyze revenue by country
        country_revenue = filtered_df.groupby('Country').agg({
            'TotalAmount': 'sum',
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique'
        }).nlargest(limit, 'TotalAmount').reset_index()
        
        for idx, row in country_revenue.iterrows():
            country_df = filtered_df[filtered_df['Country'] == row['Country']]
            avg_transaction = country_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()
            
            revenue_potential = float(row['TotalAmount'] * 1.1)  # 10% growth
            
            revenue_analysis.append({
                "country": row['Country'],
                "total_revenue": float(row['TotalAmount']),
                "transaction_count": int(row['InvoiceNo']),
                "customer_count": int(row['CustomerID']),
                "avg_transaction_value": float(avg_transaction) if not pd.isna(avg_transaction) else 0.0,
                "revenue_potential": revenue_potential
            })
        
        return jsonify({
            "success": True,
            "revenue_analysis": revenue_analysis,
            "analysis_type": "country_revenue",
            "filters_applied": filters
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/seasonal_data', methods=['GET'])
@cache_response(max_age=1800)
def get_seasonal_data():
    """Seasonal patterns analysis"""
    try:
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        # Monthly analysis
        monthly_data = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i, month in enumerate(month_names, 1):
            month_df = filtered_df[filtered_df['Month'] == i]
            if not month_df.empty:
                monthly_data.append({
                    "month": i,
                    "month_name": month,
                    "revenue": float(month_df['TotalAmount'].sum()),
                    "transactions": int(month_df['InvoiceNo'].nunique()),
                    "product_variety": int(month_df['Description'].nunique()),
                    "avg_transaction": float(month_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()) if not month_df.empty else 0.0
                })
            else:
                monthly_data.append({
                    "month": i,
                    "month_name": month,
                    "revenue": 0.0,
                    "transactions": 0,
                    "product_variety": 0,
                    "avg_transaction": 0.0
                })
        
        # Country analysis
        country_data = []
        country_stats = filtered_df.groupby('Country').agg({
            'TotalAmount': 'sum',
            'InvoiceNo': 'nunique',
            'CustomerID': 'nunique'
        }).reset_index()
        
        for _, row in country_stats.iterrows():
            country_df = filtered_df[filtered_df['Country'] == row['Country']]
            avg_transaction = country_df.groupby('InvoiceNo')['TotalAmount'].sum().mean()
            
            country_data.append({
                "country": row['Country'],
                "revenue": float(row['TotalAmount']),
                "transactions": int(row['InvoiceNo']),
                "customers": int(row['CustomerID']),
                "avg_transaction_value": float(avg_transaction) if not pd.isna(avg_transaction) else 0.0
            })
        
        country_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Hourly analysis
        hourly_data = []
        hours_in_data = sorted([h for h in filtered_df['Hour'].unique() if pd.notna(h)])
        
        for hour in hours_in_data:
            hour_df = filtered_df[filtered_df['Hour'] == hour]
            if not hour_df.empty:
                hourly_data.append({
                    "hour": int(hour),
                    "hour_label": f"{int(hour):02d}:00",
                    "transactions": int(hour_df['InvoiceNo'].nunique()),
                    "revenue": float(hour_df['TotalAmount'].sum())
                })
        
        # Weekday analysis
        weekday_data = []
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_short = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for i, day in enumerate(weekdays):
            day_df = filtered_df[filtered_df['Weekday'] == day]
            if not day_df.empty:
                weekday_data.append({
                    "weekday": day,
                    "weekday_short": weekday_short[i],
                    "transactions": int(day_df['InvoiceNo'].nunique()),
                    "revenue": float(day_df['TotalAmount'].sum())
                })
        
        # Calculate insights
        best_month = "N/A"
        peak_hour = "N/A"
        top_country = "N/A"
        best_weekday = "N/A"
        
        if monthly_data:
            best_month_data = max(monthly_data, key=lambda x: x['revenue'])
            best_month = best_month_data['month_name']
        
        if hourly_data:
            peak_hour_data = max(hourly_data, key=lambda x: x['transactions'])
            peak_hour = peak_hour_data['hour_label']
        
        if country_data:
            top_country_data = max(country_data, key=lambda x: x['revenue'])
            top_country = top_country_data['country']
        
        if weekday_data:
            best_weekday_data = max(weekday_data, key=lambda x: x['revenue'])
            best_weekday = best_weekday_data['weekday']
        
        return jsonify({
            "success": True,
            "monthly_data": monthly_data,
            "country_data": country_data[:10],
            "hourly_data": hourly_data,
            "weekday_data": weekday_data,
            "seasonal_insights": {
                "best_month": best_month,
                "peak_hour": peak_hour,
                "top_country": top_country,
                "best_weekday": best_weekday
            },
            "filters_applied": filters
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/frequent_itemsets', methods=['GET'])
@cache_response(max_age=600)
def get_frequent_itemsets():
    """Get frequent itemsets for network graph"""
    try:
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        # Get top products
        top_products = filtered_df['Description'].value_counts().head(20).index.tolist()
        
        nodes = []
        links = []
        
        # Create nodes
        for i, product in enumerate(top_products):
            product_revenue = filtered_df[filtered_df['Description'] == product]['TotalAmount'].sum()
            product_transactions = filtered_df[filtered_df['Description'] == product]['InvoiceNo'].nunique()
            
            product_group = min(3, (product_transactions // 5) + 1) if product_transactions > 0 else 1
            
            nodes.append({
                "id": product[:30].replace(" ", "_"),
                "name": product[:30],
                "group": product_group,
                "value": float(product_revenue / 1000),
                "transactions": product_transactions,
                "revenue": float(product_revenue)
            })
        
        # Create links
        for i in range(len(top_products)):
            for j in range(i+1, min(i+5, len(top_products))):
                product1 = top_products[i]
                product2 = top_products[j]
                
                invoices1 = set(filtered_df[filtered_df['Description'] == product1]['InvoiceNo'].unique())
                invoices2 = set(filtered_df[filtered_df['Description'] == product2]['InvoiceNo'].unique())
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
                "links_count": len(links),
                "filters_applied": filters
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
        
        # Apply filters
        filters = {
            'country': request.args.get('country', 'all'),
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'hour': request.args.get('hour', 'all'),
            'product': request.args.get('product', 'all')
        }
        
        filtered_df = apply_filters(df, filters)
        
        # Calculate top products
        top_products_df = (filtered_df.groupby('Description')['TotalAmount']
                          .agg(['sum', 'count', 'mean'])
                          .rename(columns={'sum': 'total_revenue', 'count': 'transactions', 'mean': 'avg_price'})
                          .sort_values('total_revenue', ascending=False)
                          .head(limit)
                          .reset_index())
        
        products_list = []
        for idx, row in top_products_df.iterrows():
            product_df = filtered_df[filtered_df['Description'] == row['Description']]
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
            "products": products_list,
            "filters_applied": filters
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/filters', methods=['GET'])
@cache_response(max_age=3600)
def get_filters():
    """Get available filters"""
    try:
        countries = [str(c) for c in df['Country'].unique().tolist() if pd.notna(c)][:30]
        years = [int(y) for y in sorted(df['Year'].unique().tolist()) if pd.notna(y)]
        
        # Get months present in data
        months_present = [int(m) for m in sorted(df['Month'].unique().tolist()) if pd.notna(m) and 1 <= m <= 12]
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_filters = [{"value": i, "name": month_names[i-1]} for i in months_present if 1 <= i <= 12]
        
        # Get hours present in data
        hours_present = [int(h) for h in sorted(df['Hour'].unique().tolist()) if pd.notna(h) and 0 <= h <= 23]
        
        # Get top products for product filter
        top_products = df['Description'].value_counts().head(50).index.tolist()
        
        filters = {
            "countries": countries,
            "years": years,
            "months": month_filters,
            "hours": hours_present,
            "products": top_products,
            "weekdays": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }
        
        return jsonify({"success": True, "filters": filters})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# APPLICATION STARTUP
# ============================================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("INTELLIGENT PRODUCT ASSORTMENT DASHBOARD")
    print("="*60)
    print(f"📊 Total Records: {len(df):,}")
    print(f"🛒 Total Transactions: {df['InvoiceNo'].nunique():,}")
    print(f"📦 Total Products: {df['Description'].nunique():,}")
    print(f"💰 Total Revenue: ${df['TotalAmount'].sum():,.2f}")
    print("\n🚀 AVAILABLE ENDPOINTS:")
    print("   • /api/health - Health check")
    print("   • /api/summary - Data summary")
    print("   • /api/association_rules - Association rules")
    print("   • /api/suggested_bundles - Product bundles")
    print("   • /api/revenue_analysis - Revenue analysis")
    print("   • /api/seasonal_data - Seasonal patterns")
    print("   • /api/frequent_itemsets - Network graph")
    print("   • /api/top_products - Top products")
    print("   • /api/filters - Available filters")
    print("\n🔧 Press Ctrl+C to stop")
    print("="*60)
    
    app.run(debug=True, port=5000, host='0.0.0.0', threaded=True)