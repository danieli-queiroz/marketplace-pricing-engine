# marketplace-pricing-engine

# 🚀 Multi-Marketplace Pricing Engine

An advanced backend logic built with **Python** to automate price calculations, fee breakdowns, and profit margin analysis for major e-commerce platforms (**Mercado Livre**, **Shopee**, and **SHEIN**).

> **Note:** This is a portfolio project demonstrating backend logic, service-controller architecture, and complex business rule implementation.

## 💡 The Problem
E-commerce sellers struggle to calculate the real profit of a product due to dynamic variables:
* Variable commission rates per marketplace.
* Complex shipping tables based on weight.
* Specific rules for new sellers or high-volume accounts.
* Tax thresholds and fixed fees.

## 🛠️ The Solution
I built a centralized **Pricing Engine** that ingests product data (cost, weight, tax rate) and returns a detailed financial analysis for each platform, including a **Reverse Pricing Algorithm** to suggest the optimal sale price based on a desired profit margin.

## ✨ Key Features

### 1. Multi-Platform Logic
* **Mercado Livre:** Handles logic for "Classic" vs. "Premium" listings and looks up shipping costs based on weight tables (0.5kg to 5kg+).
* **Shopee:** Implements the R$ 100.00 commission cap, specific rules for CPF vs. CNPJ sellers, and volume-based fixed fees (R$ 4.00 vs R$ 7.00).
* **SHEIN:** Automatically detects "New Sellers" (< 30 days) to apply tax exemptions (0% commission).

### 2. Reverse Pricing (Smart Suggestion)
If a user wants a specific Net Profit Margin (e.g., 20%), the system reverse-engineers the calculation to tell exactly **what price to set**, considering all variable taxes and fees that will be deducted.

### 3. Data Standardization
Regardless of the platform, the API returns a standardized JSON response with calculated percentages (`_pct` fields), making it easy for frontend applications to render charts and dashboards.

## 💻 Tech Stack
* **Language:** Python 3.10+
* **Architecture:** Service-Controller Pattern (Clean Code)
* **Data Handling:** JSON for decoupled business rules
* **Validation:** Pydantic (Logic)

## 📂 Project Structure
```text
├── pricing_service.py       # Core business logic & math
├── pricing_controller.py    # API Endpoint definition
├── helpers.py               # Math utility functions
├── rules_mercadolivre.json  # Configuration for ML fees & shipping
├── rules_shopee.json        # Configuration for Shopee caps & tiers
├── rules_shein.json         # Configuration for Shein exemptions
└── requirements.txt         # Dependencies
