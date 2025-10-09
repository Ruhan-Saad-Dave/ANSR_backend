from fastapi import APIRouter, Depends, HTTPException
from services.prediction import (
    get_spending_prediction,
    get_cashflow_prediction,
    get_daily_spending_trend,
    get_monthly_spending_trend,
)

router = APIRouter(tags=["Prediction"])

@router.get("/spending/{user_id}")
def predict_spending(user_id: str, timeframe: str = 'monthly'):
    """
    Predicts future expenses for a given user.

    Args:
        user_id (str): The ID of the user.
        timeframe (str, optional): The prediction timeframe. Defaults to 'monthly'.
            Options: 'daily', 'weekly', 'monthly'.

    Returns:
        dict: A dictionary containing the predicted expenses.
    """
    if timeframe not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(status_code=400, detail="Invalid timeframe. Use 'daily', 'weekly', or 'monthly'.")

    prediction = get_spending_prediction(user_id, timeframe)
    
    if "message" in prediction:
        if prediction["message"] == "Not enough data for a reliable prediction.":
            raise HTTPException(status_code=404, detail=prediction["message"])
        else:
            raise HTTPException(status_code=500, detail=prediction["message"])
            
    return {"user_id": user_id, "timeframe": timeframe, "prediction": prediction}

@router.get("/cashflow/{user_id}")
def predict_cashflow(user_id: str, timeframe: str = 'monthly'):
    """
    Predicts future cashflow for a given user.

    Args:
        user_id (str): The ID of the user.
        timeframe (str, optional): The prediction timeframe. Defaults to 'monthly'.
            Options: 'daily', 'weekly', 'monthly'.

    Returns:
        dict: A dictionary containing the predicted cashflow.
    """
    if timeframe not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(status_code=400, detail="Invalid timeframe. Use 'daily', 'weekly', or 'monthly'.")

    prediction = get_cashflow_prediction(user_id, timeframe)
    
    if "message" in prediction:
        if prediction["message"] == "Not enough data for a reliable prediction.":
            raise HTTPException(status_code=404, detail=prediction["message"])
        else:
            raise HTTPException(status_code=500, detail=prediction["message"])
            
    return {"user_id": user_id, "timeframe": timeframe, "prediction": prediction}

@router.get("/spending/trend/daily/{user_id}")
def daily_spending_trend(user_id: str):
    """
    Gets the daily spending trend for the last 7 days.

    Args:
        user_id (str): The ID of the user.

    Returns:
        dict: A dictionary containing the daily spending trend.
    """
    trend = get_daily_spending_trend(user_id)
    
    if "message" in trend:
        raise HTTPException(status_code=500, detail=trend["message"])
            
    return {"user_id": user_id, "daily_spending_trend": trend}

@router.get("/spending/trend/monthly/{user_id}")
def monthly_spending_trend(user_id: str):
    """
    Gets the monthly spending trend for the last 12 months.

    Args:
        user_id (str): The ID of the user.

    Returns:
        dict: A dictionary containing the monthly spending trend.
    """
    trend = get_monthly_spending_trend(user_id)
    
    if "message" in trend:
        raise HTTPException(status_code=500, detail=trend["message"])
            
    return {"user_id": user_id, "monthly_spending_trend": trend}