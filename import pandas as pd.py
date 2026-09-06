import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def preprocess_data(df, id_col, aid_col, value_col, max_columns_per_aid=5):
    # Create a dictionary to store the new columns
    new_columns = {}
    for aid in df[aid_col].unique():
        aid_subset = df[df[aid_col] == aid]
        for i in range(max_columns_per_aid):
            new_columns[f'{aid}_{i}'] = aid_subset.groupby(id_col)[value_col].nth(i).fillna(0)
    
    # Combine the new columns into a single DataFrame
    result_df = pd.DataFrame(new_columns)
    result_df[id_col] = df[id_col].unique()
    
    return result_df

def main():
    # Load the data from the CSV file
    raw_data = pd.read_csv('/Users/aimaankhan/Downloads/archive-2/UNSW_NB15_training-set.csv')
    
    # Print the columns to help identify correct names
    print("Columns in the dataset:", raw_data.columns)
    
    # Define column names (replace these with the actual column names from your CSV file)
    id_col = 'id'  # Replace with the correct column name
    aid_col = 'proto'    # Replace with the correct column name
    value_col = 'dur'  # Replace with the correct column name (example value column)
    label_col = 'label'  # Replace with the correct column name
    
    # Preprocess the data
    processed_data = preprocess_data(raw_data, id_col, aid_col, value_col)
    
    # Merge labels back to the processed data
    processed_data = processed_data.merge(raw_data[[id_col, label_col]].drop_duplicates(), on=id_col, how='left')
    
    # Fill any remaining NaN values in the features
    processed_data = processed_data.fillna(0)
    
    # Define features and labels
    X = processed_data.drop(label_col, axis=1)  # Adjust column name if necessary
    y = processed_data[label_col]  # Adjust column name if necessary
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Predict and evaluate
    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    print("Accuracy Score:", accuracy_score(y_test, y_pred))

if __name__ == '__main__':
    main()
