import os
import json
from groq import AsyncGroq
from pydantic import BaseModel
from app.domain.models import TradeEntry, Profile

class DraftEmail(BaseModel):
    subject: str
    body: str

class CommunicationService:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    async def draft_broker_email(self, entry: TradeEntry, profile: Profile) -> DraftEmail:
        prompt = f"""
        Draft a professional email to a Nigerian Customs Broker requesting their service.
        
        Business Name: {profile.business_name}
        Product: {entry.product_name}
        Quantity: {entry.quantity} {entry.unit}
        FOB Value: ${entry.value_usd}
        Suggested HS Code: {entry.hs_code or 'Pending'}
        
        The email should state that the Form M draft is ready and attached. Keep it concise, professional, and suitable for a mobile email client.
        
        Return exactly this JSON structure:
        {{
            "subject": "Email Subject",
            "body": "Email Body Text"
        }}
        """

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional logistics assistant. Always return JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                response_format={"type": "json_object"},
            )
            
            result = json.loads(chat_completion.choices[0].message.content)
            
            return DraftEmail(
                subject=result.get("subject", "Customs Brokerage Request"),
                body=result.get("body", "Please find our Form M draft attached.")
            )
        except Exception as e:
            return DraftEmail(
                subject="Error generating draft",
                body=f"Failed to generate email draft: {str(e)}"
            )

communication_service = CommunicationService()
