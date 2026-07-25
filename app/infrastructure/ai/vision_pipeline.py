import os
import json
from groq import AsyncGroq
from app.domain.models.vision import ProductAttributes


class VisionPipeline:
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
        self.vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"

    def _strip_data_prefix(self, base64_image: str) -> str:
        if "," in base64_image:
            return base64_image.split(",", 1)[1]
        return base64_image

    async def identify_product(self, base64_image: str) -> ProductAttributes:
        image_data = self._strip_data_prefix(base64_image)

        identification = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "You are a customs classification expert. Analyze this product image and extract structured trade attributes. "
                                "Return ONLY a JSON object with these exact keys:\n"
                                "{\n"
                                '  "product_name": "proper commercial trade name",\n'
                                '  "category": "one of: food, textile, electronics, chemicals, machinery, agricultural, pharmaceutical, cosmetics, building_materials, consumer_goods, vehicles, other",\n'
                                '  "description": "one precise sentence describing this product for customs purposes",\n'
                                '  "material": "primary material composition e.g. cotton, steel, polyester, glass, or null",\n'
                                '  "brand": "brand name if visible or null",\n'
                                '  "weight_class": "light/medium/heavy or null",\n'
                                '  "purpose": "primary use e.g. food consumption, industrial, medical, personal care",\n'
                                '  "origin_cues": "any visible country of origin text or manufacturing markings or null",\n'
                                '  "packaging": "describe packaging: bulk, retail box, sachet, bottle, bag, or null",\n'
                                '  "condition": "new/used/refurbished"\n'
                                "}"
                            ),
                        },
                    ],
                }
            ],
            model=self.vision_model,
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        raw = json.loads(identification.choices[0].message.content)
        return ProductAttributes(**raw)


vision_pipeline = VisionPipeline()
