"""
EDA Analysis Script
Generates visualizations from the ecommerce dataset
Run this to create all figures without Jupyter
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
data_path = PROJECT_ROOT / 'data' / 'ecommerce_user_behavior_8000.csv'
figures_dir = PROJECT_ROOT / 'figures'
figures_dir.mkdir(exist_ok=True)

print("🚀 Starting EDA Analysis...\n")

# 1. Load data
print("📊 Loading data...")
df = pd.read_csv(data_path)
print(f"   Shape: {df.shape}")
print(f"   Columns: {len(df.columns)}")

# 2. Missing values
print("\n❌ Checking missing values...")
missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({
    'Column': missing.index,
    'Missing_Count': missing.values,
    'Missing_Percent': missing_pct.values
}).sort_values('Missing_Count', ascending=False)

if missing.sum() > 0:
    missing_df_filtered = missing_df[missing_df['Missing_Count'] > 0]
    print(f"   Found missing values in {len(missing_df_filtered)} columns")
    
    plt.figure(figsize=(10, 6))
    plt.barh(missing_df_filtered['Column'], missing_df_filtered['Missing_Percent'], color='coral')
    plt.xlabel('Missing Percentage (%)')
    plt.title('Missing Values Distribution')
    plt.tight_layout()
    plt.savefig(figures_dir / '01_missing_values.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✅ Saved: figures/01_missing_values.png")

# 3. Target distribution
print("\n🎯 Analyzing target variable...")
df_clean = df[df['ad_clicked'].notna()]
print(f"   Valid records: {len(df_clean)}")
print(f"   Ad Clicked: {(df_clean['ad_clicked']==1).sum()} ({(df_clean['ad_clicked']==1).sum()/len(df_clean)*100:.1f}%)")
print(f"   Ad Not Clicked: {(df_clean['ad_clicked']==0).sum()} ({(df_clean['ad_clicked']==0).sum()/len(df_clean)*100:.1f}%)")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Count plot
df_clean['ad_clicked'].value_counts().plot(kind='bar', ax=axes[0], color=['#FF6B6B', '#4ECDC4'])
axes[0].set_title('Ad Clicked Distribution', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Ad Clicked')
axes[0].set_ylabel('Count')
axes[0].set_xticklabels(['No', 'Yes'], rotation=0)

# Pie chart
df_clean['ad_clicked'].value_counts().plot(kind='pie', ax=axes[1], autopct='%1.1f%%',
                                             labels=['Yes', 'No'], colors=['#4ECDC4', '#FF6B6B'])
axes[1].set_title('Ad Clicked Ratio', fontsize=12, fontweight='bold')
axes[1].set_ylabel('')

plt.tight_layout()
plt.savefig(figures_dir / '02_target_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✅ Saved: figures/02_target_distribution.png")

# 4. Numerical features
print("\n🔢 Analyzing numerical features...")
numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
if 'user_id' in numerical_cols:
    numerical_cols.remove('user_id')

fig, axes = plt.subplots(3, 4, figsize=(16, 12))
axes = axes.flatten()

for idx, col in enumerate(numerical_cols[:12]):
    axes[idx].hist(df[col].dropna(), bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    axes[idx].set_title(f'{col}', fontweight='bold')
    axes[idx].set_xlabel('Value')
    axes[idx].set_ylabel('Frequency')
    axes[idx].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(figures_dir / '03_numerical_distributions.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✅ Saved: figures/03_numerical_distributions.png")

# 5. Features vs Target
print("\n🔗 Comparing features with target...")
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

features_to_plot = ['age', 'time_on_site', 'pages_viewed', 'previous_purchases', 'avg_session_time', 'bounce_rate']

for idx, col in enumerate(features_to_plot):
    if col in df_clean.columns:
        df_clean.boxplot(column=col, by='ad_clicked', ax=axes[idx])
        axes[idx].set_title(f'{col} vs Ad Clicked', fontweight='bold')
        axes[idx].set_xlabel('Ad Clicked')
        axes[idx].set_ylabel(col)
        plt.sca(axes[idx])
        plt.xticks([1, 2], ['No', 'Yes'])

plt.suptitle('', fontsize=1)
plt.tight_layout()
plt.savefig(figures_dir / '04_features_vs_target.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✅ Saved: figures/04_features_vs_target.png")

# 6. Categorical features vs target
print("\n🏷️  Analyzing categorical features...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Gender vs Ad Clicked
pd.crosstab(df_clean['gender'], df_clean['ad_clicked']).plot(kind='bar', ax=axes[0], color=['#FF6B6B', '#4ECDC4'])
axes[0].set_title('Gender vs Ad Clicked', fontweight='bold')
axes[0].set_xlabel('Gender')
axes[0].set_ylabel('Count')
axes[0].legend(['No', 'Yes'])
plt.sca(axes[0])
plt.xticks(rotation=45)

# Device Type vs Ad Clicked
pd.crosstab(df_clean['device_type'], df_clean['ad_clicked']).plot(kind='bar', ax=axes[1], color=['#FF6B6B', '#4ECDC4'])
axes[1].set_title('Device Type vs Ad Clicked', fontweight='bold')
axes[1].set_xlabel('Device Type')
axes[1].set_ylabel('Count')
axes[1].legend(['No', 'Yes'])
plt.sca(axes[1])
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig(figures_dir / '05_categorical_vs_target.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✅ Saved: figures/05_categorical_vs_target.png")

# 7. Correlation matrix
print("\n📈 Computing correlation matrix...")
corr_matrix = df_clean.corr(numeric_only=True)
correlations = df_clean.corr(numeric_only=True)['ad_clicked'].sort_values(ascending=False)

plt.figure(figsize=(12, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
            cbar_kws={'label': 'Correlation'}, square=True)
plt.title('Feature Correlation Matrix', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig(figures_dir / '06_correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()
print("   ✅ Saved: figures/06_correlation_matrix.png")

# Summary
print("\n" + "="*60)
print("📊 KEY FINDINGS FROM EDA")
print("="*60)
print(f"\n1. DATASET SIZE:")
print(f"   Total Records: {len(df)}")
print(f"   Missing Target: {df['ad_clicked'].isnull().sum()}")
print(f"   Usable Records: {len(df_clean)}")

print(f"\n2. TARGET BALANCE:")
print(f"   Ad Clicked: {(df_clean['ad_clicked']==1).sum()} ({(df_clean['ad_clicked']==1).sum()/len(df_clean)*100:.1f}%)")
print(f"   Ad Not Clicked: {(df_clean['ad_clicked']==0).sum()} ({(df_clean['ad_clicked']==0).sum()/len(df_clean)*100:.1f}%)")

print(f"\n3. TOP PREDICTIVE FEATURES (by correlation):")
top_corr = correlations.drop('ad_clicked').abs().nlargest(5)
for i, col in enumerate(top_corr.index, 1):
    print(f"   {i}. {col}: {correlations[col]:.3f}")

print(f"\n4. DATA QUALITY:")
print(f"   Missing Values: {len(missing_df[missing_df['Missing_Count'] > 0])} columns")
print(f"   Numerical Features: {len(numerical_cols)}")
print(f"   Categorical Features: {len([c for c in df.columns if df[c].dtype == 'object'])}")

print("\n✅ EDA ANALYSIS COMPLETE!")
print("\nGenerated visualizations:")
for i in range(1, 7):
    print(f"   - figures/0{i}_*.png")
