"""
Intelligent Product Assortment Dashboard using Market Basket Analysis
Backend API Implementation

Features Implemented:
1. Market Basket Analysis (Apriori Algorithm)
2. Association Rules Generation
3. Suggested Product Bundles
4. Revenue Analysis for Bundles
5. Seasonal Assortment Analysis
6. Dynamic Filters (Country, Time, etc.)
7. Network Graph Data Generation (Frequent Itemsets)
8. Top Products Analysis
9. Interactive Dashboard Support

Tech Stack:
- Flask (REST API)
- Pandas (Data Processing)
- mlxtend (Apriori Algorithm)
- NumPy (Numerical Operations)
"""

import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from mlxtend.frequent_patterns import apriori, association_rules
import warnings
import os
import traceback
from datetime import datetime
import time
from functools import lru_cache

warnings.filterwarnings('ignore')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend

# ============================================================================
# FEATURE 1: DATA LOADING AND PREPROCESSING
# ============================================================================
print("Loading data for Intelligent Product Assortment Dashboard...")
try:
    # Find data file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_path = os.path.join(project_root, 'data', 'Online_Retail_Cleaned.csv')
    
    print(f"Looking for data at: {data_path}")
    
    if os.path.exists(data_path):
        # Load CSV data
        df = pd.read_csv(data_path)
        print(f"✅ CSV data loaded successfully! Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Data optimization for better performance
        numeric_cols = ['Quantity', 'UnitPrice', 'TotalAmount', 'Year', 'Month', 'Day', 'Hour']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Remove invalid transactions (negative quantities/prices)
        df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
        
        print(f"✅ Data optimized. Shape after cleaning: {df.shape}")
    else:
        print(f"❌ File not found at: {data_path}")
        raise FileNotFoundError("Data file not found")
        
except Exception as e:
    # Fallback to sample data if CSV not found
    print(f"Error loading data: {e}")
    print("Creating minimal sample data for testing...")
    np.random.seed(42)
    n_samples = 10000
    df = pd.DataFrame({
        'InvoiceNo': [f'INV{i:06d}' for i in np.random.randint(1, 5000, n_samples)],
        'StockCode': [f'SKU{np.random.randint(1000, 9999)}' for _ in range(n_samples)],
        'Description': np.random.choice([f'Product {chr(65+i)}' for i in range(26)], n_samples),
        'Quantity': np.random.randint(1, 10, n_samples),
        'UnitPrice': np.random.uniform(1, 100, n_samples),
        'CustomerID': [f'CUST{np.random.randint(1, 1000):05d}' for _ in range(n_samples)],
        'Country': np.random.choice(['UK', 'Germany', 'France', 'Italy', 'Spain', 'USA'], n_samples),
        'TotalAmount': np.random.uniform(10, 500, n_samples),
        'Year': np.random.choice([2010, 2011], n_samples),
        'Month': np.random.randint(1, 13, n_samples),
        'Day': np.random.randint(1, 29, n_samples),
        'Weekday': np.random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                                     'Friday', 'Saturday', 'Sunday'], n_samples),
        'Hour': np.random.randint(8, 20, n_samples)
    })
    df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
    print("✅ Sample data created!")

# ============================================================================
# FEATURE 2: CACHING MECHANISM FOR PERFORMANCE
# ============================================================================
@lru_cache(maxsize=32)
def get_filtered_data(country=None, year=None, month=None, hour=None):
    """
    Get filtered data with caching for better performance.
    This supports dynamic filtering feature.
    
    Args:
        country: Filter by country
        year: Filter by year
        month: Filter by month
        hour: Filter by hour
    
    Returns:
        Filtered pandas DataFrame
    """
    filtered = df.copy()
    
    # Apply dynamic filters
    if country and country != 'all':
        filtered = filtered[filtered['Country'] == country]
    if year and year != 'all':
        filtered = filtered[filtered['Year'] == int(year)]
    if month and month != 'all':
        filtered = filtered[filtered['Month'] == int(month)]
    if hour and hour != 'all':
        filtered = filtered[filtered['Hour'] == int(hour)]
    
    return filtered

# ============================================================================
# FEATURE 3: DASHBOARD API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        "message": "Intelligent Product Assortment Dashboard API",
        "status": "running",
        "data_size": len(df),
        "features": [
            "Market Basket Analysis (Apriori Algorithm)",
            "Association Rules Generation",
            "Suggested Product Bundles",
            "Revenue Analysis for Bundles",
            "Seasonal Assortment Analysis",
            "Dynamic Filters",
            "Network Graph Data",
            "Top Products Analysis"
        ],
        "endpoints": {
            "/api/summary": "GET - Get data summary statistics",
            "/api/association_rules": "GET - Get association rules (Market Basket Analysis)",
            "/api/suggested_bundles": "GET - Get suggested product bundles",
            "/api/revenue_analysis": "GET - Get revenue analysis for bundles",
            "/api/seasonal_data": "GET - Get seasonal assortment data",
            "/api/filters": "GET - Get available dynamic filters",
            "/api/top_products": "GET - Get top products by revenue/quantity",
            "/api/frequent_itemsets": "GET - Get frequent itemsets for network graph",
            "/api/health": "GET - Health check endpoint"
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_records": len(df),
        "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
    })

# ============================================================================
# FEATURE 4: MARKET BASKET ANALYSIS - ASSOCIATION RULES
# ============================================================================
@app.route('/api/association_rules', methods=['GET'])
def get_association_rules():
    """
    Get association rules using Apriori algorithm.
    This is the core Market Basket Analysis implementation.
    
    Query Parameters:
        min_support: Minimum support threshold (default: 0.02)
        min_confidence: Minimum confidence threshold (default: 0.3)
        country: Filter by country
        year: Filter by year
        month: Filter by month
    
    Returns:
        JSON with association rules containing:
        - antecedents: Items that lead to purchase
        - consequents: Items that are purchased together
        - support: Frequency of itemset occurrence
        - confidence: Probability of consequent given antecedent
        - lift: Improvement over random chance
    """
    try:
        # Get parameters with defaults
        min_support = float(request.args.get('min_support', 0.02))
        min_confidence = float(request.args.get('min_confidence', 0.3))
        country = request.args.get('country', 'all')
        year = request.args.get('year', 'all')
        month = request.args.get('month', 'all')
        
        start_time = time.time()
        
        # Apply dynamic filters
        filtered_df = get_filtered_data(country, year, month, None)
        
        # Check if enough data exists
        if len(filtered_df) < 100:
            return jsonify({
                "success": True,
                "data": [],
                "message": "Insufficient data for analysis",
                "processing_time": time.time() - start_time
            })
        
        # Sample data for faster processing (performance optimization)
        sample_size = min(20000, len(filtered_df))
        sample_df = filtered_df.sample(sample_size, random_state=42)
        
        # Step 1: Create basket data - Transform to transaction format
        # Group by InvoiceNo and Description, sum quantities, pivot to basket format
        basket = (sample_df.groupby(['InvoiceNo', 'Description'])['Quantity']
                  .sum().unstack().reset_index().fillna(0)
                  .set_index('InvoiceNo'))
        
        # Step 2: Convert to binary format (1 = purchased, 0 = not purchased)
        basket_sets = basket.applymap(lambda x: 1 if x > 0 else 0)
        
        # Step 3: Filter products with minimum transactions
        min_transactions = max(10, min_support * len(basket_sets))
        basket_sets = basket_sets.loc[:, basket_sets.sum() > min_transactions]
        
        if len(basket_sets.columns) < 2:
            return jsonify({
                "success": True,
                "data": [],
                "message": "Not enough product variety for association rules",
                "processing_time": time.time() - start_time
            })
        
        # Step 4: Generate frequent itemsets using Apriori algorithm
        frequent_itemsets = apriori(basket_sets, 
                                   min_support=min_support, 
                                   use_colnames=True, 
                                   max_len=2)  # Limit to pairs for simplicity
        
        if len(frequent_itemsets) == 0:
            return jsonify({
                "success": True,
                "data": [],
                "message": "No frequent itemsets found",
                "processing_time": time.time() - start_time
            })
        
        # Step 5: Generate association rules from frequent itemsets
        rules = association_rules(frequent_itemsets, 
                                 metric="confidence", 
                                 min_threshold=min_confidence)
        
        # Step 6: Format rules for JSON response
        simple_rules = []
        for _, rule in rules.iterrows():
            antecedents = list(rule['antecedents'])
            consequents = list(rule['consequents'])
            
            simple_rules.append({
                "antecedents": antecedents,
                "consequents": consequents,
                "support": float(rule['support']),
                "confidence": float(rule['confidence']),
                "lift": float(rule['lift']),
                "antecedent_count": len(antecedents),
                "consequent_count": len(consequents)
            })
        
        # Sort by lift (most meaningful rules first)
        simple_rules.sort(key=lambda x: x['lift'], reverse=True)
        
        return jsonify({
            "success": True,
            "data": simple_rules[:50],  # Limit to top 50 rules
            "total_rules": len(simple_rules),
            "sample_size": sample_size,
            "processing_time": round(time.time() - start_time, 2),
            "parameters": {
                "min_support": min_support,
                "min_confidence": min_confidence,
                "country": country,
                "year": year,
                "month": month
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "processing_time": time.time() - start_time
        })

# ============================================================================
# FEATURE 5: SUGGESTED PRODUCT BUNDLES
# ============================================================================
@app.route('/api/suggested_bundles', methods=['GET'])
def get_suggested_bundles():
    """
    Generate suggested product bundles based on association rules.
    This implements intelligent product assortment recommendations.
    
    Query Parameters:
        min_confidence: Minimum confidence for bundle suggestions
    
    Returns:
        JSON with suggested bundles including:
        - bundle_id: Unique identifier
        - products: List of products in bundle
        - confidence: Rule confidence
        - lift: Rule lift
        - estimated_revenue: Estimated revenue from bundle
    """
    try:
        min_confidence = float(request.args.get('min_confidence', 0.5))
        
        # Get association rules first
        rules_response = get_association_rules()
        rules_data = json.loads(rules_response.get_data())
        
        if not rules_data['success']:
            return jsonify(rules_data)
        
        rules = rules_data['data']
        
        bundles = []
        for i, rule in enumerate(rules[:20]):  # Process top 20 rules
            antecedents = rule['antecedents']
            consequents = rule['consequents']
            
            # Combine antecedents and consequents to create bundle
            all_products = antecedents + consequents
            
            # Get pricing and quantity data for bundle
            product_data = df[df['Description'].isin(all_products)]
            
            if not product_data.empty:
                avg_price = product_data['UnitPrice'].mean()
                avg_quantity = product_data['Quantity'].mean()
                
                # Estimate revenue from this bundle
                estimated_revenue = avg_price * avg_quantity * len(all_products)
                
                bundles.append({
                    "bundle_id": f"B{i+1:03d}",
                    "products": all_products,
                    "confidence": rule['confidence'],
                    "lift": rule['lift'],
                    "support": rule['support'],
                    "estimated_revenue": round(estimated_revenue, 2),
                    "bundle_size": len(all_products),
                    "avg_product_price": round(avg_price, 2)
                })
        
        return jsonify({
            "success": True,
            "bundles": bundles,
            "total_bundles": len(bundles),
            "avg_bundle_size": round(np.mean([b['bundle_size'] for b in bundles]), 2) if bundles else 0
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# FEATURE 6: REVENUE ANALYSIS FOR BUNDLES
# ============================================================================
@app.route('/api/revenue_analysis', methods=['GET'])
def get_revenue_analysis():
    """
    Perform revenue analysis for suggested bundles.
    This helps in business decision making for bundle pricing.
    
    Returns:
        JSON with revenue analysis including:
        - total_revenue: Actual revenue from bundle products
        - transaction_count: Number of transactions
        - avg_transaction_value: Average transaction value
        - estimated_bundle_revenue: Estimated revenue if sold as bundle
    """
    try:
        # Get suggested bundles first
        bundles_response = get_suggested_bundles()
        bundles_data = json.loads(bundles_response.get_data())
        
        if not bundles_data['success']:
            return jsonify(bundles_data)
        
        bundles = bundles_data['bundles']
        
        revenue_analysis = []
        for bundle in bundles[:10]:  # Analyze top 10 bundles
            products = bundle['products']
            
            # Find all transactions containing these products
            product_transactions = df[df['Description'].isin(products)]
            
            # Calculate metrics
            transaction_count = product_transactions['InvoiceNo'].nunique()
            total_revenue = product_transactions['TotalAmount'].sum()
            avg_transaction = total_revenue / max(1, transaction_count)
            
            revenue_analysis.append({
                "bundle_id": bundle['bundle_id'],
                "bundle_name": " + ".join([str(p) for p in products[:3]]) + 
                              (f" + {len(products)-3} more" if len(products) > 3 else ""),
                "total_revenue": round(total_revenue, 2),
                "transaction_count": transaction_count,
                "avg_transaction_value": round(avg_transaction, 2),
                "confidence": bundle['confidence'],
                "estimated_bundle_revenue": bundle['estimated_revenue'],
                "revenue_potential": round(bundle['estimated_revenue'] - total_revenue, 2)
            })
        
        # Sort by total revenue (highest first)
        revenue_analysis.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        return jsonify({
            "success": True,
            "revenue_analysis": revenue_analysis,
            "total_bundles_analyzed": len(revenue_analysis),
            "total_potential_revenue": round(sum([r['revenue_potential'] for r in revenue_analysis]), 2)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# FEATURE 7: SEASONAL ASSORTMENT ANALYSIS
# ============================================================================
@app.route('/api/seasonal_data', methods=['GET'])
def get_seasonal_data():
    """
    Analyze seasonal patterns in product assortment.
    This helps in inventory planning and seasonal promotions.
    
    Returns:
        JSON with seasonal data including:
        - Monthly revenue and transaction patterns
        - Hourly shopping patterns
        - Country-wise performance
        - Weekday patterns
    """
    try:
        # Monthly analysis
        monthly_data = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month in range(1, 13):
            month_df = df[df['Month'] == month]
            if len(month_df) > 0:
                monthly_revenue = month_df['TotalAmount'].sum()
                transaction_count = month_df['InvoiceNo'].nunique()
                
                monthly_data.append({
                    "month": month,
                    "month_name": month_names[month-1],
                    "revenue": round(monthly_revenue, 2),
                    "transactions": transaction_count,
                    "avg_transaction": round(monthly_revenue / max(1, transaction_count), 2),
                    "product_variety": month_df['Description'].nunique()
                })
        
        # Hourly analysis (time-based assortment)
        hourly_data = []
        for hour in range(0, 24):
            hour_df = df[df['Hour'] == hour]
            if len(hour_df) > 0:
                hourly_data.append({
                    "hour": hour,
                    "hour_label": f"{hour:02d}:00",
                    "transactions": hour_df['InvoiceNo'].nunique(),
                    "revenue": round(hour_df['TotalAmount'].sum(), 2),
                    "avg_basket_size": round(hour_df['Quantity'].mean(), 2)
                })
        
        # Country analysis (geographic assortment)
        country_data = []
        top_countries = df['Country'].value_counts().head(10).index.tolist()
        for country in top_countries:
            country_df = df[df['Country'] == country]
            country_data.append({
                "country": country,
                "revenue": round(country_df['TotalAmount'].sum(), 2),
                "transactions": country_df['InvoiceNo'].nunique(),
                "customers": country_df['CustomerID'].nunique(),
                "avg_transaction_value": round(country_df.groupby('InvoiceNo')['TotalAmount'].sum().mean(), 2)
            })
        
        # Weekday analysis
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                        'Friday', 'Saturday', 'Sunday']
        weekday_data = []
        for weekday in weekday_names:
            weekday_df = df[df['Weekday'] == weekday]
            if len(weekday_df) > 0:
                weekday_data.append({
                    "weekday": weekday,
                    "weekday_short": weekday[:3],
                    "transactions": weekday_df['InvoiceNo'].nunique(),
                    "revenue": round(weekday_df['TotalAmount'].sum(), 2),
                    "avg_basket_value": round(weekday_df['TotalAmount'].mean(), 2)
                })
        
        return jsonify({
            "success": True,
            "monthly_data": monthly_data,
            "hourly_data": hourly_data,
            "country_data": country_data,
            "weekday_data": weekday_data,
            "seasonal_insights": {
                "best_month": max(monthly_data, key=lambda x: x['revenue'])['month_name'] if monthly_data else "N/A",
                "peak_hour": max(hourly_data, key=lambda x: x['transactions'])['hour_label'] if hourly_data else "N/A",
                "top_country": max(country_data, key=lambda x: x['revenue'])['country'] if country_data else "N/A",
                "best_weekday": max(weekday_data, key=lambda x: x['revenue'])['weekday'] if weekday_data else "N/A",
                "seasonal_variation": round(np.std([m['revenue'] for m in monthly_data]) / 
                                          np.mean([m['revenue'] for m in monthly_data]), 3) if monthly_data else 0
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# FEATURE 8: DYNAMIC FILTERS
# ============================================================================
@app.route('/api/filters', methods=['GET'])
def get_filters():
    """
    Get available dynamic filters for the dashboard.
    This enables interactive filtering by various dimensions.
    
    Returns:
        JSON with all available filter options
    """
    try:
        filters = {
            "countries": sorted(df['Country'].dropna().unique().tolist()),
            "years": sorted(df['Year'].dropna().astype(int).unique().tolist()),
            "months": [
                {"value": i, "name": month_name}
                for i, month_name in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)
                if i in df['Month'].unique()
            ],
            "hours": sorted(df['Hour'].dropna().astype(int).unique().tolist()),
            "weekdays": sorted(df['Weekday'].dropna().unique().tolist()),
            "price_ranges": [
                {"min": 0, "max": 10, "label": "Under $10"},
                {"min": 10, "max": 50, "label": "$10 - $50"},
                {"min": 50, "max": 100, "label": "$50 - $100"},
                {"min": 100, "max": float('inf'), "label": "Over $100"}
            ]
        }
        
        return jsonify({
            "success": True, 
            "filters": filters,
            "total_options": {
                "countries": len(filters["countries"]),
                "years": len(filters["years"]),
                "months": len(filters["months"]),
                "hours": len(filters["hours"])
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# FEATURE 9: TOP PRODUCTS ANALYSIS
# ============================================================================
@app.route('/api/top_products', methods=['GET'])
def get_top_products():
    """
    Get top products by revenue and quantity.
    This helps in identifying best-selling products.
    
    Query Parameters:
        limit: Number of top products to return
    
    Returns:
        JSON with top products by revenue and quantity
    """
    try:
        limit = int(request.args.get('limit', 20))
        
        # Clean product descriptions
        df_clean = df.copy()
        df_clean['Description'] = df_clean['Description'].astype(str).str.strip()
        
        # Top products by revenue
        top_by_revenue = (df_clean.groupby('Description')['TotalAmount']
                         .agg(['sum', 'count', 'mean'])
                         .rename(columns={'sum': 'total_revenue', 
                                         'count': 'transaction_count',
                                         'mean': 'avg_transaction_value'})
                         .sort_values('total_revenue', ascending=False)
                         .head(limit)
                         .reset_index())
        
        # Top products by quantity sold
        top_by_quantity = (df_clean.groupby('Description')['Quantity']
                          .agg(['sum', 'count', 'mean'])
                          .rename(columns={'sum': 'total_quantity',
                                         'count': 'transaction_count',
                                         'mean': 'avg_quantity_per_transaction'})
                          .sort_values('total_quantity', ascending=False)
                          .head(limit)
                          .reset_index())
        
        return jsonify({
            "success": True,
            "top_by_revenue": top_by_revenue.to_dict('records'),
            "top_by_quantity": top_by_quantity.to_dict('records'),
            "insights": {
                "highest_revenue_product": top_by_revenue.iloc[0]['Description'] if len(top_by_revenue) > 0 else "N/A",
                "highest_quantity_product": top_by_quantity.iloc[0]['Description'] if len(top_by_quantity) > 0 else "N/A",
                "revenue_range": f"${top_by_revenue['total_revenue'].min():.2f} - ${top_by_revenue['total_revenue'].max():.2f}" if len(top_by_revenue) > 0 else "N/A"
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# FEATURE 10: FREQUENT ITEMSETS FOR NETWORK GRAPH
# ============================================================================
@app.route('/api/frequent_itemsets', methods=['GET'])
def get_frequent_itemsets():
    """
    Get frequent itemsets for network graph visualization.
    This provides data for visualizing product relationships.
    
    Query Parameters:
        min_support: Minimum support threshold
        country: Filter by country
        year: Filter by year
        month: Filter by month
    
    Returns:
        JSON with frequent itemsets for network graph
    """
    try:
        min_support = float(request.args.get('min_support', 0.02))
        country = request.args.get('country', 'all')
        year = request.args.get('year', 'all')
        month = request.args.get('month', 'all')
        
        # Get filtered data
        filtered_df = get_filtered_data(country, year, month, None)
        
        if len(filtered_df) < 100:
            return jsonify({
                "success": True,
                "data": [],
                "message": "Insufficient data for analysis"
            })
        
        # Sample data for performance
        sample_size = min(10000, len(filtered_df))
        sample_df = filtered_df.sample(sample_size, random_state=42)
        
        # Create basket data
        basket = (sample_df.groupby(['InvoiceNo', 'Description'])['Quantity']
                  .sum().unstack().reset_index().fillna(0)
                  .set_index('InvoiceNo'))
        
        # Convert to binary
        basket_sets = basket.applymap(lambda x: 1 if x > 0 else 0)
        
        # Filter products
        min_transactions = max(10, min_support * len(basket_sets))
        basket_sets = basket_sets.loc[:, basket_sets.sum() > min_transactions]
        
        if len(basket_sets.columns) < 2:
            return jsonify({
                "success": True,
                "data": [],
                "message": "Not enough product variety"
            })
        
        # Generate frequent itemsets (up to 3 items for network graph)
        frequent_itemsets = apriori(basket_sets, 
                                   min_support=min_support, 
                                   use_colnames=True, 
                                   max_len=3)
        
        # Format for network graph
        itemsets_list = []
        for _, row in frequent_itemsets.iterrows():
            items = list(row['itemsets'])
            itemsets_list.append({
                "items": items,
                "support": float(row['support']),
                "item_count": len(items),
                "nodes": [{"id": item, "group": 1} for item in items],
                "links": [{"source": items[i], "target": items[j], "value": float(row['support'])}
                         for i in range(len(items)) for j in range(i+1, len(items))]
            })
        
        # Sort by support
        itemsets_list.sort(key=lambda x: x['support'], reverse=True)
        
        return jsonify({
            "success": True,
            "data": itemsets_list[:50],  # Top 50 itemsets
            "network_data": {
                "nodes": list(set([node for itemset in itemsets_list 
                                 for node in itemset['items']])),
                "links": [link for itemset in itemsets_list 
                         for link in itemset['links']]
            },
            "total_itemsets": len(itemsets_list),
            "sample_size": sample_size,
            "graph_ready": len(itemsets_list) > 0
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# FEATURE 11: DATA SUMMARY
# ============================================================================
@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get comprehensive data summary statistics"""
    try:
        summary = {
            "total_transactions": int(df['InvoiceNo'].nunique()),
            "total_products": int(df['Description'].nunique()),
            "total_customers": int(df['CustomerID'].nunique()),
            "total_revenue": float(df['TotalAmount'].sum()),
            "avg_transaction_value": float(df.groupby('InvoiceNo')['TotalAmount'].sum().mean()),
            "total_countries": int(df['Country'].nunique()),
            "date_range": {
                "min_year": int(df['Year'].min()),
                "max_year": int(df['Year'].max()),
                "total_months": int(df['Month'].nunique()),
                "time_period": f"{df['Year'].min()} - {df['Year'].max()}"
            },
            "data_quality": {
                "total_records": len(df),
                "null_customers": int(df['CustomerID'].isnull().sum()),
                "null_descriptions": int(df['Description'].isnull().sum()),
                "data_completeness": round((1 - df['Description'].isnull().sum() / len(df)) * 100, 2)
            },
            "business_metrics": {
                "avg_items_per_transaction": round(df.groupby('InvoiceNo')['Quantity'].sum().mean(), 2),
                "avg_price_per_item": round(df['UnitPrice'].mean(), 2),
                "revenue_per_customer": round(df['TotalAmount'].sum() / df['CustomerID'].nunique(), 2),
                "repeat_customer_rate": round(df['CustomerID'].value_counts()[df['CustomerID'].value_counts() > 1].count() / 
                                            df['CustomerID'].nunique() * 100, 2)
            }
        }
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ============================================================================
# APPLICATION STARTUP
# ============================================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("INTELLIGENT PRODUCT ASSORTMENT DASHBOARD")
    print("Market Basket Analysis Backend API")
    print("="*60)
    print(f"📊 Total Records: {len(df):,}")
    print(f"🛒 Total Transactions: {df['InvoiceNo'].nunique():,}")
    print(f"📦 Total Products: {df['Description'].nunique():,}")
    print(f"👥 Total Customers: {df['CustomerID'].nunique():,}")
    print(f"🌍 Total Countries: {df['Country'].nunique():,}")
    print(f"💰 Total Revenue: ${df['TotalAmount'].sum():,.2f}")
    print(f"💾 Memory Usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    print("="*60)
    print("\n🚀 Starting server on http://localhost:5000")
    print("📋 Available Features:")
    print("   • Market Basket Analysis (Apriori Algorithm)")
    print("   • Association Rules Generation")
    print("   • Suggested Product Bundles")
    print("   • Revenue Analysis")
    print("   • Seasonal Assortment")
    print("   • Dynamic Filtering")
    print("   • Network Graph Data")
    print("   • Top Products Analysis")
    print("\n🔧 Press Ctrl+C to stop")
    print("="*60)
    
    # Start Flask server
    app.run(debug=True, port=5000, host='0.0.0.0')