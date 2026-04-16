from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=8000)
    mode: str = "public"
    stream: bool = False

    def to_internal(self) -> dict:
        is_public = self.mode == "public"

        return {
            "sessionId": self.session_id,
            "userId": self.user_id,
            "message": self.message,
            "stream": self.stream,
            "policy": {
                "publicMode": is_public,
                "tools": {
                    "shell": False if is_public else False,
                    "browser": False if is_public else False,
                    "fileWrite": False if is_public else False,
                },
            },
        }