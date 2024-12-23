# toxicity_predictor.py
import subprocess

class ToxicityPredictor:
    async def predict(self, preprocessed_chat_message, model_path="model.vw"):
        """Predict the toxicity of a message using Vowpal Wabbit."""
        vw_formatted_message = f"|text {preprocessed_chat_message}"

        # Run VW for prediction
        result = subprocess.run(
            [
                "vw",
                "--quiet",
                "-i",
                model_path,
                "-t",
                "--predictions",
                "/dev/stdout",
                "--link",
                "logistic",
            ],
            input=vw_formatted_message.encode("utf-8"),
            capture_output=True,
        )

        # Parse the output to get prediction
        prediction = float(result.stdout.decode("utf-8").strip())
        return prediction

