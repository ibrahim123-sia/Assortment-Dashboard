<<<<<<< HEAD
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
=======
# 🛒 Intelligent Product Assortment Dashboard  
### Market Basket Analysis • Association Rules • Clustering • Revenue Optimization

This project is an **end-to-end analytical dashboard** that helps retailers understand **customer buying patterns**, discover **frequently purchased product combinations**, and generate **data-driven product bundles** to optimize revenue and assortment planning.

Built using:
- **React** (Frontend)
- **FastAPI + Python** (Backend)
- **FP-Growth / Apriori** (Market Basket Analysis)
- **K-Means / Clustering** (Product & seasonal groupings)

---

## 🚀 Features

### 🔹 **1. Market Basket Analysis**
Uses **FP-Growth or Apriori** algorithm to generate:
- Frequent itemsets  
- Association rules (support, confidence, lift)  
- Item-to-item relationships  

### 🔹 **2. Network Graph Visualization**
Interactive graph where:
- Nodes = Products  
- Edges = Strength of association  

### 🔹 **3. Suggested Product Bundles**
AI-generated bundles based on:
- Lift  
- Confidence  
- Co-purchase behavior  

Helps design cross-sell strategies.

### 🔹 **4. Revenue Impact Analysis**
For each suggested bundle:
- Current revenue  
- Opportunity revenue  
- Projected uplift  

### 🔹 **5. Seasonal Assortment Analysis**
Identifies:
- Summer vs winter products  
- Time-based buying patterns  
- Monthly demand trends  

### 🔹 **6. Product Clustering**
Clusters products based on:
- Sales behavior  
- Co-purchase similarity  
- Seasonality  

### 🔹 **7. Dynamic Filters**
Filter all analytics by:
- Store  
- Region  
- Time (month/season)  
- Category  
- Price range  

---

**Backend Responsibilities:**
- Data cleaning & transformation  
- Running FP-Growth/Apriori  
- Building association rules  
- Product clustering  
- Seasonal analysis  
- Revenue calculations  
- Exposing results via REST API  

**Frontend Responsibilities:**
- Network graph visualization  
- Interactive tables, filters, charts  
- Rendering bundles & revenue impact  
- Seasonal dashboards  

---

## 🧰 Tech Stack

### **Frontend**
- React  
- Recharts / D3.js  
- TailwindCSS / Material UI  

### **Backend**
- FastAPI  
- Python  
- Pandas  
- mlxtend / efficient-apriori / PyFPGrowth  
- Scikit-learn (for clustering)
>>>>>>> 30544f6a1e8f2eb48f0f8cb08c04315e6330fcdf
