import calendar
import io
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def visualize_monthly_expenses_bar(df):
    """Generates a bar chart of total expenses per month."""
    expenses_df = df[df['payment_type'] == 'expense'].copy()
    if expenses_df.empty:
        return None

    monthly_expenses = expenses_df.groupby('month')['amount'].sum().reset_index()
    month_map = {i: calendar.month_name[i] for i in range(1, 13)}
    monthly_expenses['month_name'] = monthly_expenses['month'].map(month_map)
    monthly_expenses = monthly_expenses.sort_values('month')

    plt.figure(figsize=(12, 7))
    sns.barplot(x='month_name', y='amount', data=monthly_expenses, palette='viridis', hue='month_name', dodge=False)
    plt.title('Total Amount Spent per Month', fontsize=16)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Total Amount Spent', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend([], [], frameon=False)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def visualize_daily_expenses_line(df):
    """Generates a line chart of total expenses per day."""
    expenses_df = df[df['payment_type'] == 'expense'].copy()
    expenses_df.dropna(subset=['year', 'month', 'date'], inplace=True)
    if expenses_df.empty:
        return None

    expenses_df[['year', 'month', 'date']] = expenses_df[['year', 'month', 'date']].astype(int)
    expenses_df['transaction_date'] = pd.to_datetime(expenses_df[['year', 'month', 'date']].rename(columns={'date': 'day'}))
    daily_expenses = expenses_df.groupby('transaction_date')['amount'].sum().reset_index()
    daily_expenses = daily_expenses.sort_values('transaction_date')

    plt.figure(figsize=(14, 7))
    sns.lineplot(x='transaction_date', y='amount', data=daily_expenses, marker='o', color='b')
    plt.title('Daily Expense Trend', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Total Amount Spent', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def visualize_category_pie(df):
    """Generates a pie chart of expense distribution by category."""
    expenses_df = df[df['payment_type'] == 'expense'].copy()
    expenses_df.dropna(subset=['category'], inplace=True)
    if expenses_df.empty:
        return None

    category_expenses = expenses_df.groupby('category')['amount'].sum()
    
    plt.figure(figsize=(10, 8))
    plt.pie(
        category_expenses,
        labels=category_expenses.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=sns.color_palette('pastel'),
        wedgeprops={'edgecolor': 'white'}
    )
    plt.title('Expense Distribution by Category', fontsize=16)
    plt.axis('equal')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def visualize_payment_method_pie(df):
    """Generates a pie chart of expense distribution by payment method."""
    expenses_df = df[df['payment_type'] == 'expense'].copy()
    expenses_df.dropna(subset=['payment_method'], inplace=True)
    if expenses_df.empty:
        return None

    payment_method_expenses = expenses_df.groupby('payment_method')['amount'].sum()

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f'{pct:.1f}%\n(${val:,.0f})'
        return my_autopct

    plt.figure(figsize=(12, 9))
    plt.pie(
        payment_method_expenses,
        labels=payment_method_expenses.index,
        autopct=make_autopct(payment_method_expenses),
        startangle=140,
        colors=sns.color_palette('pastel'),
        wedgeprops={'edgecolor': 'white'}
    )
    plt.title('Expense Distribution by Payment Method', fontsize=16)
    plt.axis('equal')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf
