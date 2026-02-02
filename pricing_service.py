import os
import json
from helpers import percentage_of, percent_from_total, percentage_division, percentage_multiplication

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class PricingCalculatorService:

    def calculate_price(self, data):
        # 1. Mercado Livre
        ml_premium = self.calculate_ml(data, logistics_type="padrao", listing_type="premium")
        ml_classic = self.calculate_ml(data, logistics_type="padrao", listing_type="classico")
        
        # 2. Shopee
        shopee_result = self.calculate_shopee(data)

        # 3. Shein
        shein_result = self.calculate_shein(data)

        return [ml_premium, ml_classic, shopee_result, shein_result]

    def calculate_ml(self, data, logistics_type, listing_type):
        json_data = self._load_rules("rules_mercadolivre.json")
        rules = json_data.get("ml_rules", {})

        ml_commission = rules.get("commissions", {}).get(listing_type, 0.17)
        logistics = rules.get("logistics_rules", {}).get(logistics_type, {})

        fee_table = logistics.get("fee_table", [])
        free_shipping_limit = logistics.get("free_shipping_limit", 79.00)
        weight_shipping_table = rules.get("estimated_seller_shipping", {})

        bite_percentage = (ml_commission + (data.tax_percent / 100) + (data.ads_investment_percent / 100))

        analysis_result = {}
        if data.current_sale_price is not None and data.current_sale_price > 0:
            fixed_fee = self._get_fixed_fee(data.current_sale_price, fee_table)
            
            if fixed_fee == -1:
                analysis_result = {"error": "Invalid price (Blocked)."}
                
            shipping_cost = self._calculate_seller_shipping(
                data.current_sale_price, free_shipping_limit, data.weight_kg, weight_shipping_table
            )

            bite_value = data.current_sale_price * bite_percentage
            total_costs = bite_value + fixed_fee + shipping_cost + data.product_cost + data.packaging_cost
            profit = data.current_sale_price - total_costs

            analysis_result = {
                "analyzed_price": data.current_sale_price,
                "fixed_fee": round(fixed_fee, 2),
                "fixed_fee_pct": percent_from_total(fixed_fee, data.current_sale_price),
                "tax": round(percentage_division(data.tax_percent) * data.current_sale_price, 2),
                "tax_pct": data.tax_percent,
                "ads": round(percentage_division(data.ads_investment_percent) * data.current_sale_price, 2),
                "ads_pct": data.ads_investment_percent,
                "commission": round(ml_commission * data.current_sale_price, 2),
                "commission_pct": percentage_multiplication(ml_commission),
                "shipping": round(shipping_cost, 2),
                "shipping_pct": percent_from_total(shipping_cost, data.current_sale_price),
                "product_cost": round(data.product_cost, 2),
                "product_cost_pct": percent_from_total(data.product_cost, data.current_sale_price),
                "packaging_cost": round(data.packaging_cost, 2),
                "packaging_cost_pct": percent_from_total(data.packaging_cost, data.current_sale_price),
                "total_costs": round(total_costs, 2),
                "total_costs_pct": percent_from_total(total_costs, data.current_sale_price),
                "real_profit": round(profit, 2),
                "profit_pct": percent_from_total(profit, data.current_sale_price),
            }

        suggestion_result = {}
        if data.desired_margin is not None and data.desired_margin > 0:
            target_margin = percentage_division(data.desired_margin)
            divisor = 1 - bite_percentage - target_margin

            if divisor > 0:
                estimated_price = (data.product_cost + data.packaging_cost) / divisor
                real_fee = self._get_fixed_fee(estimated_price, fee_table)
                shipping_cost = self._calculate_seller_shipping(
                    estimated_price, free_shipping_limit, data.weight_kg, weight_shipping_table
                )
                base_cost = data.product_cost + data.packaging_cost + real_fee + shipping_cost
                final_price = base_cost / divisor

                ads = round(percentage_division(data.ads_investment_percent) * final_price, 2)
                tax = round(percentage_division(data.tax_percent) * final_price, 2)
                commission = round(ml_commission * final_price, 2)
                total_costs = round(base_cost + ads + tax + commission, 2)

                suggestion_result = {
                    "target_margin_percent": data.desired_margin,
                    "suggested_price": round(final_price, 2),
                    "fixed_fee": round(real_fee, 2),
                    "fixed_fee_pct": percent_from_total(real_fee, final_price),
                    "tax": tax, "tax_pct": data.tax_percent,
                    "ads": ads, "ads_pct": data.ads_investment_percent,
                    "commission": commission, "commission_pct": percentage_multiplication(ml_commission),
                    "shipping": round(shipping_cost, 2), "shipping_pct": percent_from_total(shipping_cost, final_price),
                    "product_cost": round(data.product_cost, 2), "product_cost_pct": percent_from_total(data.product_cost, final_price),
                    "packaging_cost": round(data.packaging_cost, 2), "packaging_cost_pct": percent_from_total(data.packaging_cost, final_price),
                    "total_costs": round(total_costs, 2), "total_costs_pct": percent_from_total(total_costs, final_price),
                    "real_profit": round(final_price - total_costs, 2),
                    "profit_pct": percent_from_total(final_price - total_costs, final_price),
                }

        return {
            "marketplace": "Mercado Livre",
            "logistics_type": logistics_type,
            "listing_type": listing_type,
            "current_analysis": analysis_result,
            "price_suggestion": suggestion_result,
        }

    def calculate_shopee(self, data):
        json_data = self._load_rules("rules_shopee.json")
        rules = json_data.get("shopee_rules", {})
        pcts = rules.get("percentages", {})
        fixed = rules.get("fixed_fees", {})
        limits = rules.get("limits", {})

        shopee_rate = pcts.get("base_commission", 0.14)
        if hasattr(data, 'use_free_shipping') and data.use_free_shipping:
            shopee_rate += pcts.get("free_shipping_program", 0.06)

        base_fixed = fixed.get("standard", 4.00)    

        is_high_volume = False
        if hasattr(data, 'is_cpf') and data.is_cpf:
            if hasattr(data, 'orders_last_90_days') and data.orders_last_90_days > limits.get("cpf_high_volume_threshold_orders", 450):
                base_fixed += fixed.get("cpf_extra", 3.00)
                is_high_volume = True

        analysis_result = {}
        if data.current_sale_price is not None and data.current_sale_price > 0:
            final_fixed_fee = self._get_shopee_fixed_fee(data.current_sale_price, base_fixed, limits)
            raw_commission = data.current_sale_price * shopee_rate
            commission_val = min(raw_commission, limits.get("commission_cap", 100.00))
            tax_val = percentage_division(data.tax_percent) * data.current_sale_price
            ads_val = percentage_division(data.ads_investment_percent) * data.current_sale_price
            total_costs = commission_val + final_fixed_fee + tax_val + ads_val + data.product_cost + data.packaging_cost
            profit = data.current_sale_price - total_costs
            
            analysis_result = {
                "analyzed_price": data.current_sale_price,
                "real_profit": round(profit, 2), "profit_pct": percent_from_total(profit, data.current_sale_price),
                "commission": round(commission_val, 2), "commission_pct": percent_from_total(commission_val, data.current_sale_price),
                "fixed_fee": round(final_fixed_fee, 2), "fixed_fee_pct": percent_from_total(final_fixed_fee, data.current_sale_price),
                "tax": round(tax_val, 2), "tax_pct": data.tax_percent,
                "ads": round(ads_val, 2), "ads_pct": data.ads_investment_percent,
                "product_cost": round(data.product_cost, 2), "product_cost_pct": percent_from_total(data.product_cost, data.current_sale_price),
                "packaging_cost": round(data.packaging_cost, 2), "packaging_cost_pct": percent_from_total(data.packaging_cost, data.current_sale_price),
                "total_costs": round(total_costs, 2), "total_costs_pct": percent_from_total(total_costs, data.current_sale_price),
            }

        suggestion_result = {}
        if data.desired_margin is not None and data.desired_margin > 0:
            price_guess = data.product_cost * 2
            for _ in range(10):
                curr_fixed = self._get_shopee_fixed_fee(price_guess, base_fixed, limits)
                raw_comm = price_guess * shopee_rate
                curr_comm = min(raw_comm, limits.get("commission_cap", 100.00))
                base_cash_needed = (data.product_cost + data.packaging_cost + curr_fixed + curr_comm)
                divisor = 1 - percentage_division(data.tax_percent) - percentage_division(data.ads_investment_percent) - percentage_division(data.desired_margin)
                if divisor > 0:
                    new_price = base_cash_needed / divisor
                    if abs(new_price - price_guess) < 0.05:
                        price_guess = new_price
                        break
                    price_guess = new_price
            
            final_fixed = self._get_shopee_fixed_fee(price_guess, base_fixed, limits)
            final_comm = min(price_guess * shopee_rate, limits.get("commission_cap", 100.00))
            tax_val = percentage_division(data.tax_percent) * price_guess
            ads_val = percentage_division(data.ads_investment_percent) * price_guess
            total_est_cost = data.product_cost + data.packaging_cost + final_fixed + final_comm + tax_val + ads_val
        
            suggestion_result = {
                "target_margin_percent": data.desired_margin,
                "suggested_price": round(price_guess, 2),
                "fixed_fee": round(final_fixed, 2), "fixed_fee_pct": percent_from_total(final_fixed, price_guess),
                "tax": round(tax_val, 2), "tax_pct": data.tax_percent,
                "ads": round(ads_val, 2), "ads_pct": data.ads_investment_percent,
                "commission": round(final_comm, 2), "commission_pct": percent_from_total(final_comm, price_guess),
                "product_cost": round(data.product_cost, 2), "product_cost_pct": percent_from_total(data.product_cost, price_guess),
                "packaging_cost": round(data.packaging_cost, 2), "packaging_cost_pct": percent_from_total(data.packaging_cost, price_guess),
                "total_costs": round(total_est_cost, 2), "total_costs_pct": percent_from_total(total_est_cost, price_guess),
                "real_profit": round(price_guess - total_est_cost, 2), "profit_pct": percent_from_total(price_guess - total_est_cost, price_guess),
            }

        return {
            "marketplace": "Shopee",
            "listing_type": "Standard", 
            "seller_type": "High Volume CPF" if is_high_volume else "Standard",
            "current_analysis": analysis_result,
            "price_suggestion": suggestion_result
        }
    
    def calculate_shein(self, data):
        json_data = self._load_rules("rules_shein.json")
        rules = json_data.get("shein_rules", {})
        pcts = rules.get("percentages", {})
        limits = rules.get("limits", {})

        shein_rate = pcts.get("standard_commission", 0.16)
        is_new_seller = False
        days = getattr(data, 'shein_days_since_registration', 999)
        if days <= limits.get("new_seller_days_limit", 30):
            shein_rate = pcts.get("new_seller_commission", 0.00)
            is_new_seller = True

        fixed_fee_val = 0.0
        analysis_result = {}
        if data.current_sale_price is not None and data.current_sale_price > 0:
            commission_val = data.current_sale_price * shein_rate
            tax_val = percentage_division(data.tax_percent) * data.current_sale_price
            ads_val = percentage_division(data.ads_investment_percent) * data.current_sale_price
            total_costs = commission_val + fixed_fee_val + tax_val + ads_val + data.product_cost + data.packaging_cost
            profit = data.current_sale_price - total_costs
            
            analysis_result = {
                "analyzed_price": data.current_sale_price,
                "fixed_fee": round(fixed_fee_val, 2), "fixed_fee_pct": percent_from_total(fixed_fee_val, data.current_sale_price),
                "tax": round(tax_val, 2), "tax_pct": data.tax_percent,
                "ads": round(ads_val, 2), "ads_pct": data.ads_investment_percent,
                "commission": round(commission_val, 2), "commission_pct": percent_from_total(commission_val, data.current_sale_price),
                "product_cost": round(data.product_cost, 2), "product_cost_pct": percent_from_total(data.product_cost, data.current_sale_price),
                "packaging_cost": round(data.packaging_cost, 2), "packaging_cost_pct": percent_from_total(data.packaging_cost, data.current_sale_price),
                "total_costs": round(total_costs, 2), "total_costs_pct": percent_from_total(total_costs, data.current_sale_price),
                "real_profit": round(profit, 2), "profit_pct": percent_from_total(profit, data.current_sale_price),
            }

        suggestion_result = {}
        if data.desired_margin is not None and data.desired_margin > 0:
            numerator = data.product_cost + data.packaging_cost + fixed_fee_val
            denominator = 1 - percentage_division(data.tax_percent) - percentage_division(data.ads_investment_percent) - percentage_division(data.desired_margin) - shein_rate
            
            if denominator > 0:
                price_suggested = numerator / denominator
                commission_final = price_suggested * shein_rate
                tax_final = percentage_division(data.tax_percent) * price_suggested
                ads_final = percentage_division(data.ads_investment_percent) * price_suggested
                total_est_cost = data.product_cost + data.packaging_cost + commission_final + tax_final + ads_final
                
                suggestion_result = {
                    "target_margin_percent": data.desired_margin,
                    "suggested_price": round(price_suggested, 2),
                    "fixed_fee": round(fixed_fee_val, 2), "fixed_fee_pct": percent_from_total(fixed_fee_val, price_suggested),
                    "tax": round(tax_final, 2), "tax_pct": data.tax_percent,
                    "ads": round(ads_final, 2), "ads_pct": data.ads_investment_percent,
                    "commission": round(commission_final, 2), "commission_pct": percent_from_total(commission_final, price_suggested),
                    "product_cost": round(data.product_cost, 2), "product_cost_pct": percent_from_total(data.product_cost, price_suggested),
                    "packaging_cost": round(data.packaging_cost, 2), "packaging_cost_pct": percent_from_total(data.packaging_cost, price_suggested),
                    "total_costs": round(total_est_cost, 2), "total_costs_pct": percent_from_total(total_est_cost, price_suggested),
                    "real_profit": round(price_suggested - total_est_cost, 2), "profit_pct": percent_from_total(price_suggested - total_est_cost, price_suggested),
                }

        return {
            "marketplace": "SHEIN",
            "listing_type": "Standard",
            "seller_type": "New Seller (0% Comm)" if is_new_seller else "Standard (16%)",
            "current_analysis": analysis_result,
            "price_suggestion": suggestion_result
        }          

    def _load_rules(self, filename="rules_mercadolivre.json"):
        try:
            path = os.path.join(BASE_DIR, filename) 
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
        
    def _get_shopee_fixed_fee(self, price, base_fee, limits):
        if base_fee >= 7.00 and price < limits.get("regressive_threshold_price", 12.00):
             diff = 12.00 - price
             discount = diff * 0.25
             return max(base_fee - discount, 0.0)
        
        if base_fee < 7.00 and price < limits.get("standard_low_value_threshold", 8.00):
            return price * 0.50
        return base_fee      

    def _get_fixed_fee(self, price: float, fee_table: list) -> float:
        if price <= 0: return 0.0
        fee_table.sort(key=lambda x: x.get("opValue", 0))
        for range_item in fee_table:
            if range_item.get("operator") == ">" and price > range_item.get("opValue"):
                return range_item.get("value") if range_item.get("type") == "fixo" else -1
            elif range_item.get("operator") == "<=" and price <= range_item.get("opValue"):
                return range_item.get("value") if range_item.get("type") == "fixo" else -1
        return 0.0

    def _calculate_seller_shipping(self, price, free_limit, weight, shipping_table):
        if price >= free_limit:
            weight_key = "0.5"
            if weight > 0.5: weight_key = "1.0"
            if weight > 1.0: weight_key = "2.0"
            if weight > 2.0: weight_key = "5.0"
            return shipping_table.get(weight_key, 18.00)
        return 0.0