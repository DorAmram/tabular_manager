from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
from typing import List, Dict, Any, Optional
import io
import os

app = FastAPI(title="Tabular Data API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demonstration
data_store: Dict[str, pd.DataFrame] = {}

class DataUpload(BaseModel):
    name: str
    data: List[Dict[str, Any]]

class FilterRequest(BaseModel):
    dataset_name: str
    column: str
    operation: str  # eq, gt, lt, contains
    value: Any

class AggregateRequest(BaseModel):
    dataset_name: str
    column: str
    operation: str  # sum, mean, median, count, min, max

@app.get("/")
def read_root():
    return {"message": "Tabular Data API", "version": "1.0.0"}

@app.get("/api/datasets")
def list_datasets():
    """List all available datasets"""
    datasets = {}
    for name, df in data_store.items():
        datasets[name] = {
            "rows": len(df),
            "columns": list(df.columns),
            "shape": df.shape
        }
    return datasets

@app.post("/api/datasets")
def create_dataset(data_upload: DataUpload):
    """Create a new dataset from JSON data"""
    try:
        df = pd.DataFrame(data_upload.data)
        data_store[data_upload.name] = df
        return {
            "message": f"Dataset '{data_upload.name}' created successfully",
            "shape": df.shape,
            "columns": list(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/datasets/{dataset_name}")
def get_dataset(dataset_name: str, limit: Optional[int] = 100):
    """Get dataset data"""
    if dataset_name not in data_store:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = data_store[dataset_name]
    limited_df = df.head(limit) if limit else df

    return {
        "data": limited_df.to_dict(orient="records"),
        "columns": list(df.columns),
        "total_rows": len(df),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }

@app.delete("/api/datasets/{dataset_name}")
def delete_dataset(dataset_name: str):
    """Delete a dataset"""
    if dataset_name not in data_store:
        raise HTTPException(status_code=404, detail="Dataset not found")

    del data_store[dataset_name]
    return {"message": f"Dataset '{dataset_name}' deleted successfully"}

@app.post("/api/filter")
def filter_data(request: FilterRequest):
    """Filter dataset based on conditions"""
    if request.dataset_name not in data_store:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = data_store[request.dataset_name]

    if request.column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.column}' not found")

    try:
        if request.operation == "eq":
            filtered_df = df[df[request.column] == request.value]
        elif request.operation == "gt":
            filtered_df = df[df[request.column] > request.value]
        elif request.operation == "lt":
            filtered_df = df[df[request.column] < request.value]
        elif request.operation == "contains":
            filtered_df = df[df[request.column].astype(str).str.contains(str(request.value), na=False)]
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")

        return {
            "data": filtered_df.to_dict(orient="records"),
            "total_rows": len(filtered_df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/aggregate")
def aggregate_data(request: AggregateRequest):
    """Perform aggregation on dataset"""
    if request.dataset_name not in data_store:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = data_store[request.dataset_name]

    if request.column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.column}' not found")

    try:
        if request.operation == "sum":
            result = df[request.column].sum()
        elif request.operation == "mean":
            result = df[request.column].mean()
        elif request.operation == "median":
            result = df[request.column].median()
        elif request.operation == "count":
            result = df[request.column].count()
        elif request.operation == "min":
            result = df[request.column].min()
        elif request.operation == "max":
            result = df[request.column].max()
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")

        return {
            "column": request.column,
            "operation": request.operation,
            "result": float(result) if pd.notna(result) else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/datasets/{dataset_name}/stats")
def get_statistics(dataset_name: str):
    """Get statistical summary of dataset"""
    if dataset_name not in data_store:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = data_store[dataset_name]
    stats = df.describe(include='all').to_dict()

    return {
        "statistics": stats,
        "null_counts": df.isnull().sum().to_dict()
    }

# Initialize with sample data
sample_data = [
    {"id": 1, "name": "Alice", "age": 30, "city": "New York", "salary": 75000},
    {"id": 2, "name": "Bob", "age": 25, "city": "San Francisco", "salary": 85000},
    {"id": 3, "name": "Charlie", "age": 35, "city": "Los Angeles", "salary": 65000},
    {"id": 4, "name": "Diana", "age": 28, "city": "New York", "salary": 90000},
    {"id": 5, "name": "Eve", "age": 32, "city": "Chicago", "salary": 72000},
]
data_store["sample"] = pd.DataFrame(sample_data)

# Mount static files (for Docker deployment)
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
