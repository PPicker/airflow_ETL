import base64
import os
import json
from google import genai
from google.genai import types
from typing import Optional, List, Dict, Any


def gemini_categorizer(name: str) -> Optional[str]:
    """
    옷 이름을 입력받아 카테고리를 분류하는 함수

    Args:
        name: 분류할 옷 이름

    Returns:
        카테고리 이름(top, bottom, outer, accessory) 또는 분류 불가능할 경우 None
    """
    try:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY2"),
        )

        model = "gemini-1.5-flash-8b"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text="""옷의 이름을 입력으로 줬을 때, 그 옷의 카테고리를 4개 중 하나로 분류해서 JSON 형식으로 응답해줘"""
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""알겠습니다. 옷 이름을 입력해주세요. 
    """
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text="""아트 이프 액츠_Tencel Two Pocket Shirt_[Charcoal]"""
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""{"category":"top"}
    """
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""Western Belt [Black]"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""{"category":"accessory"}"""),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""Art' Vintage Cap [Navy]"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""{"category":"accessory"}
    """
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""Mohair Round NeckCardigan_"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""{"category":"outer"}
    """
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""Light Wool Flared Trousers"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""{"category":"bottom"}
    """
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""회색"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""{"category":null}"""),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=name),
                ],
            ),
        ]

        # 구성 설정
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=[
                types.Part.from_text(
                    text="""top, bottom, outer, accessory 중 하나로 분류할 수 있는 경우에만 해당 값을 사용하세요:
{"category": "카테고리명"}

분류가 불확실하거나 불가능한 경우 반드시 null을 사용하세요:
{"category": null}

카테고리명은 오직 다음 중 하나여야 합니다: top, bottom, outer, accessory
애매하거나 불확실한 경우, 그리고 색상이나 스타일만 언급된 경우에는 null을 사용하세요.
"""
                ),
            ],
        )

        # API 호출 및 응답 수집
        response = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response += chunk.text

        print(response)
        # JSON 파싱 및 카테고리 추출
        json_response = json.loads(response)
        category = json_response.get("category")

        # 유효한 카테고리 목록
        valid_categories = ["top", "bottom", "outer", "accessory"]

        # 유효성 검사: 유효한 카테고리가 아니면 None 반환
        if category not in valid_categories:
            return None

        return category

    except Exception as e:
        print(f"오류 발생: {e}")
        return None  # 모든 오류 상황에서 None 반환


if __name__ == "__main__":
    # from config.env_loader import load_environment
    from dotenv import load_dotenv

    load_dotenv()
    # 테스트할 옷 이름 목록
    test_items = [
        "shirt",
        "Denim Pants",
        "Wool Coat",
        "Leather Belt",
        "회색",
        "검은색 매치할 수 있는 무언가",
    ]
    for item in test_items:
        print(f"\n{item} 분류 중...")
        category = gemini_categorizer(item)
        print(f"\n결과: '{item}'은(는) '{category}' 카테고리입니다.")
        if not category:
            print("애매함")
            print(category)
