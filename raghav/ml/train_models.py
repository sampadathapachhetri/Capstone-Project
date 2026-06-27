# train_models.py
# Trains and evaluates 5 ML models on the drug interaction
# binary classification task (interaction exists vs not).
#
# Methodology:
#   1. Split data BEFORE balancing (train/test must reflect
#      real-world class distribution in the test set)
#   2. Balance ONLY the training set using SMOTE
#   3. Use 5-fold cross-validation on training data
#   4. Evaluate on untouched test set using Precision/Recall/F1/ROC-AUC
#      (not just accuracy — misleading under class imbalance)


import pandas as pd
import numpy as np
import json
import os
import time

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

from ml_config import FEATURES_OUTPUT, RESULTS_DIR, TEST_SIZE, RANDOM_STATE


#  Feature columns used for training 
FEATURE_COLUMNS = [
    'enzyme_overlap_count', 'enzyme_overlap_ratio',
    'target_overlap_count', 'target_overlap_ratio',
    'drug1_enzyme_count',   'drug2_enzyme_count',
    'drug1_target_count',   'drug2_target_count'
]


def load_dataset():
    """
    Load the feature dataset built by build_features.py.

    Returns:
      X: feature matrix (DataFrame)
      y: labels (Series) — 1 = interacts, 0 = no documented interaction
    """
    print(" Loading feature dataset...")
    df = pd.read_csv(FEATURES_OUTPUT)

    X = df[FEATURE_COLUMNS]
    y = df['label']

    print(f" Loaded {len(df):,} rows")
    print(f"   Class distribution: {y.value_counts().to_dict()}")

    return X, y


def split_and_balance(X, y):
    """
    Split data into train/test, then balance ONLY the training set.

    Why split first?
      The test set must reflect real-world class proportions to
      give an honest evaluation. Balancing before splitting would
      leak synthetic SMOTE samples into the test set, making
      evaluation results overly optimistic and unreliable.

    Why balance only train?
      SMOTE generates synthetic minority-class examples. We want
      the MODEL to learn from a balanced set, but we want to
      EVALUATE it against the true, real-world imbalanced
      distribution (the test set stays untouched).

    Args:
      X, y: full feature matrix and labels

    Returns:
      X_train_balanced, y_train_balanced  → for training
      X_test, y_test                      → for evaluation (untouched)
    """
    print("\n  Splitting train/test (80/20, stratified)...")

    # stratify=y ensures both train and test keep the same
    # class ratio as the original dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(f"   Train: {len(X_train):,} rows | Test: {len(X_test):,} rows")
    print(f"   Train distribution: {y_train.value_counts().to_dict()}")
    print(f"   Test  distribution: {y_test.value_counts().to_dict()}")

    print("\n  Applying SMOTE to training set only...")
    smote = SMOTE(random_state=RANDOM_STATE)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

    print(f"   Balanced train distribution: "
          f"{pd.Series(y_train_balanced).value_counts().to_dict()}")

    return X_train_balanced, X_test, y_train_balanced, y_test


def get_models():
    """
    Define all 5 models to compare.
    Each uses reasonable default settings suitable for this
    tabular, moderately-sized dataset.

    Returns:
      dict of model_name → unfitted model object
    """
    return {
        'Logistic Regression': LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE
        ),
        'Random Forest': RandomForestClassifier(
            n_estimators=200, max_depth=15,
            random_state=RANDOM_STATE, n_jobs=-1
        ),
        'XGBoost': XGBClassifier(
            n_estimators=200, max_depth=6,
            learning_rate=0.1, random_state=RANDOM_STATE,
            eval_metric='logloss', n_jobs=-1
        ),
        'SVM': SVC(
            kernel='rbf', probability=True, random_state=RANDOM_STATE
        ),
        'Neural Network (MLP)': MLPClassifier(
            hidden_layer_sizes=(64, 32), max_iter=500,
            random_state=RANDOM_STATE, early_stopping=True
        ),
    }


def evaluate_model(model, X_test, y_test):
    """
    Evaluate a trained model on the held-out test set.

    Uses multiple metrics because accuracy alone is misleading
    under class imbalance:
      - Precision: of predicted interactions, how many were correct?
      - Recall:    of actual interactions, how many did we catch?
      - F1:        harmonic mean of precision and recall
      - ROC-AUC:   overall ability to distinguish the two classes

    Args:
      model:   trained model
      X_test, y_test: untouched test set

    Returns:
      dict of metric_name → value
    """
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]  # probability of class 1

    return {
        'accuracy'  : accuracy_score(y_test, y_pred),
        'precision' : precision_score(y_test, y_pred),
        'recall'    : recall_score(y_test, y_pred),
        'f1_score'  : f1_score(y_test, y_pred),
        'roc_auc'   : roc_auc_score(y_test, y_proba),
    }


def cross_validate_model(model, X_train, y_train, cv_folds=5):
    """
    Run k-fold cross-validation on the training set to check
    for overfitting before final evaluation.

    If CV scores vary a lot between folds, or are much higher
    than the test score later, that signals overfitting.

    Args:
      model:    unfitted model
      X_train, y_train: balanced training data
      cv_folds: number of folds (default 5)

    Returns:
      mean_f1, std_f1: average and spread of F1 across folds
    """
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='f1', n_jobs=-1)
    return scores.mean(), scores.std()


def train_all_models():
    """
    Main function — trains and evaluates all 5 models,
    prints a comparison table, and saves results to disk.
    """
    print("=" * 60)
    print("   ML MODEL COMPARISON — DRUG INTERACTION DETECTION")
    print("=" * 60)

    # Load and prepare data
    X, y = load_dataset()
    X_train_bal, X_test, y_train_bal, y_test = split_and_balance(X, y)

    # Scale features — helps SVM, Logistic Regression, Neural Network
    # converge properly (tree models like RF/XGBoost don't need this,
    # but scaling doesn't hurt them either)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_bal)
    X_test_scaled  = scaler.transform(X_test)

    models  = get_models()
    results = []

    for name, model in models.items():
        print(f"\n{'─'*60}")
        print(f"   Training: {name}")
        print(f"{'─'*60}")

        start = time.time()

        # Cross-validation check (catches overfitting early)
        cv_mean, cv_std = cross_validate_model(
            model, X_train_scaled, y_train_bal
        )
        print(f"   5-fold CV F1: {cv_mean:.4f} (± {cv_std:.4f})")

        # Train on full training set
        model.fit(X_train_scaled, y_train_bal)

        # Evaluate on held-out test set
        metrics = evaluate_model(model, X_test_scaled, y_test)

        elapsed = time.time() - start

        print(f"   Test Accuracy  : {metrics['accuracy']:.4f}")
        print(f"   Test Precision : {metrics['precision']:.4f}")
        print(f"   Test Recall    : {metrics['recall']:.4f}")
        print(f"   Test F1-Score  : {metrics['f1_score']:.4f}")
        print(f"   Test ROC-AUC   : {metrics['roc_auc']:.4f}")
        print(f"   Time taken     : {elapsed:.1f} sec")

        # Overfitting check: compare CV F1 vs Test F1
        gap = abs(cv_mean - metrics['f1_score'])
        if gap > 0.1:
            print(f"    Warning: CV/Test F1 gap = {gap:.3f} "
                  f"(possible overfitting)")
        else:
            print(f"   CV/Test F1 gap = {gap:.3f} (looks stable)")

        results.append({
            'model'        : name,
            'cv_f1_mean'   : round(cv_mean, 4),
            'cv_f1_std'    : round(cv_std, 4),
            'test_accuracy': round(metrics['accuracy'], 4),
            'test_precision': round(metrics['precision'], 4),
            'test_recall'  : round(metrics['recall'], 4),
            'test_f1'      : round(metrics['f1_score'], 4),
            'test_roc_auc' : round(metrics['roc_auc'], 4),
            'train_time_sec': round(elapsed, 1),
            'overfit_gap'  : round(gap, 4)
        })

    #  Final comparison table 
    results_df = results_to_dataframe(results)
    print("\n" + "=" * 60)
    print("   FINAL MODEL COMPARISON")
    print("=" * 60)
    print(results_df.to_string(index=False))

    # Save results
    output_path = os.path.join(RESULTS_DIR, "model_comparison.csv")
    results_df.to_csv(output_path, index=False)
    print(f"\n Results saved to: {output_path}")

    # Identify best model
    best = results_df.loc[results_df['test_f1'].idxmax()]
    print(f"\n Best model (by F1-score): {best['model']} "
          f"(F1={best['test_f1']})")

    return results_df


def results_to_dataframe(results):
    """Convert results list to a clean sorted DataFrame"""
    df = pd.DataFrame(results)
    return df.sort_values('test_f1', ascending=False)


if __name__ == "__main__":
    train_all_models()