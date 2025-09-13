from typing import Dict, Any

def is_valid_classification_json(data: Dict[str, Any]) -> bool:
    """
    Validates the structure and types of the classification JSON object returned by the LLM.

    This function ensures that the data conforms to the expected schema before it is
    integrated into the application state, preventing errors from malformed API responses.

    Args:
        data: The JSON object (as a dictionary) to validate.

    Returns:
        True if the data is valid according to the defined schema, False otherwise.
    """
    if not isinstance(data, dict):
        print("Validation Error: Top-level object is not a dictionary.")
        return False

    if "classification" not in data:
        print("Validation Error: Missing 'classification' key at the top level.")
        return False

    class_data = data["classification"]
    if not isinstance(class_data, dict):
        print("Validation Error: 'classification' value is not a dictionary.")
        return False

    required_keys = ["topic_tags", "sentiment", "priority", "confidence_scores"]
    if not all(key in class_data for key in required_keys):
        print(f"Validation Error: Missing one or more required keys in 'classification'. Expected: {required_keys}")
        return False

    if not isinstance(class_data["topic_tags"], list) or not all(isinstance(tag, str) for tag in class_data["topic_tags"]):
        print("Validation Error: 'topic_tags' must be a list of strings.")
        return False

    if not isinstance(class_data["sentiment"], str):
        print("Validation Error: 'sentiment' must be a string.")
        return False

    if not isinstance(class_data["priority"], str):
        print("Validation Error: 'priority' must be a string.")
        return False

    confidence = class_data.get("confidence_scores")
    if not isinstance(confidence, dict):
        print("Validation Error: 'confidence_scores' must be a dictionary.")
        return False

    required_confidence_keys = ["topic", "sentiment", "priority"]
    if not all(key in confidence for key in required_confidence_keys):
        print(f"Validation Error: Missing one or more keys in 'confidence_scores'. Expected: {required_confidence_keys}")
        return False

    if not all(isinstance(confidence[key], (int, float)) and 0.0 <= confidence[key] <= 1.0 for key in required_confidence_keys):
        print("Validation Error: Confidence scores must be floats between 0.0 and 1.0.")
        return False

    return True
