# database.py
import sqlite3
import pandas as pd
import os
import re

def clean_price(val):
    """Remove ₹ and commas from price strings → float"""
    if pd.isna(val):
        return None
    return float(re.sub(r'[₹,]', '', str(val)).strip())

def clean_percentage(val):
    """Remove % from discount strings → float"""
    if pd.isna(val):
        return None
    return float(str(val).replace('%', '').strip())

def clean_rating(val):
    """Convert rating to float safely"""
    try:
        return float(str(val).strip())
    except:
        return None

def clean_rating_count(val):
    """Remove commas from rating count → int"""
    if pd.isna(val):
        return None
    try:
        return int(str(val).replace(',', '').strip())
    except:
        return None

def create_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/amazon.db")

    df = pd.read_csv("data/amazon.csv")

    # ── Products table ──────────────────────────────────────────
    products = df[[
        'product_id', 'product_name', 'category',
        'discounted_price', 'actual_price', 'discount_percentage',
        'rating', 'rating_count', 'about_product', 'img_link', 'product_link'
    ]].copy()

    products['discounted_price']    = products['discounted_price'].apply(clean_price)
    products['actual_price']        = products['actual_price'].apply(clean_price)
    products['discount_percentage'] = products['discount_percentage'].apply(clean_percentage)
    products['rating']              = products['rating'].apply(clean_rating)
    products['rating_count']        = products['rating_count'].apply(clean_rating_count)

    # Split category into main and sub (format: "Main|Sub|SubSub")
    products['main_category'] = products['category'].apply(
        lambda x: str(x).split('|')[0].strip()
    )
    products['sub_category'] = products['category'].apply(
        lambda x: str(x).split('|')[1].strip() if len(str(x).split('|')) > 1 else None
    )

    products.drop_duplicates(subset='product_id', inplace=True)
    products.to_sql("products", conn, if_exists="replace", index=False)
    print(f"✅ Products table: {len(products)} rows")

    # ── Reviews table ────────────────────────────────────────────
    reviews = df[[
        'product_id', 'user_id', 'user_name',
        'review_id', 'review_title', 'review_content'
    ]].copy()

    reviews.dropna(subset=['review_id'], inplace=True)
    reviews.to_sql("reviews", conn, if_exists="replace", index=False)
    print(f"✅ Reviews table: {len(reviews)} rows")

    conn.close()
    print("\n🎉 Database ready at data/amazon.db!")
    print("Tables created: products, reviews")

if __name__ == "__main__":
    create_db()