import base64
from google import genai
from google.genai import types
from pathlib import Path
import os
from typing import List, Union
import io
from PIL import Image
from io import BytesIO
import json


def encode_file(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def convert_pil_image_for_gemini(pil_image):
    """
    PIL Image 객체를 Gemini API에서 사용할 수 있는 Part 객체로 변환합니다.

    Args:
        pil_image (PIL.Image): PIL Image 객체

    Returns:
        types.Part: Gemini API에서 사용할 수 있는 Part 객체
    """
    # BytesIO 객체에 이미지 저장
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()

    # Part 객체 생성 및 반환
    return types.Part.from_bytes(mime_type="image/jpeg", data=img_bytes)


class Analyzer:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY3"),
        )
        BASE_DIR = Path(__file__).resolve().parent
        prompt_dir = BASE_DIR.parent / "prompt_images"  # 예: main에서 한 단계 위로

        self.files = [
            self.client.files.upload(file=tmp_file)
            for tmp_file in sorted(Path(prompt_dir).glob("*"))
        ]
        self.model = "gemini-2.5-flash-preview-04-17"

    def analyze(self, images, description):
        parts = []
        for image in images:
            parts.append(convert_pil_image_for_gemini(image))

        # 설명 추가
        parts.append(types.Part.from_text(text=description))

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.files[0].uri,
                        mime_type=self.files[0].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[1].uri,
                        mime_type=self.files[1].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[2].uri,
                        mime_type=self.files[2].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[3].uri,
                        mime_type=self.files[3].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[4].uri,
                        mime_type=self.files[4].mime_type,
                    ),
                    types.Part.from_text(
                        text="""- 세미 오버 실루엣
- 가먼트 워싱
- 체크 린넨 원단
- 논카라 디테일
- 아웃포켓 디테일
- 밑단 올 풀림 디테일
- 천연 자개 단추

Brand : Art if acts
Model : Non Collar Linen French Check Shirt
Material : Linen 100%
Color : Blue/Brown

SIZE(cm)
M : 어깨 47 / 가슴 57.5 / 소매 62.5 / 총장 76
L : 어깨 49 / 가슴 60 / 소매 63.5 / 총장 77  
XL : 어깨 51 / 가슴 62.5 / 소매 64.5 / 총장 78

Model : 183cm / 65kg / Top (L size) / Bottom (M size)

- 사이즈 측정 방법에 따라 1-2cm 오차가 생길 수 있습니다.
- 모니터 설정에 따라 상이 다르게 보일 수 있습니다.
- 착장컷은 색감 보정 및 조명으로 인해 컬러가 상이해 보일 수 있는 점 안내드리며, 자세한 사항은 제품컷 참고 부탁드립니다.

"""
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""Here's my thinking process to arrive at the desired JSON output:

1.  **Understand the Goal:** The user wants a JSON object describing a piece of clothing based on provided images and text descriptions. The JSON should contain specific keys: `색상 및 패턴`, `소재`, `디테일`, `실루엣`, `분위기 및 지향점`, and `세부 카테고리`. Important constraints are:
    *   Ignore irrelevant text (brand, washing instructions, sizing, model info, disclaimers).
    *   Focus on the images to verify and extract visual information (color, pattern, silhouette, details).
    *   If the image shows a full outfit, focus only on the described item (in this case, a shirt).
    *   Combine information from both the images and the relevant text.

2.  **Analyze the Input:**
    *   **Images:** Multiple images of a male model wearing a long-sleeved shirt, a white t-shirt underneath, blue jeans, and black sandals. The shirt is the focus. It's a brown and blue checked pattern. It appears to have no collar, buttons down the front, and possibly frayed edges at the hem and cuffs.
    *   **Text Description (Relevant Parts Identified):**
        *   `- 세미 오버 실루엣` -> Silhouette
        *   `- 가먼트 워싱` -> Detail/Treatment
        *   `- 체크 린넨 원단` -> Pattern, Material
        *   `- 논카라 디테일` -> Detail
        *   `- 아웃포켓 디테일` -> Detail (Need to check images)
        *   `- 밑단 올 풀림 디테일` -> Detail
        *   `- 천연 자개 단추` -> Detail, Material/Appearance of detail
        *   `Material : Linen 100%` -> Material
        *   `Color : Blue/Brown` -> Color

3.  **Process Each JSON Key:**

    *   **`색상 및 패턴` (Color and Pattern):**
        *   *Text:* \"체크 린넨 원단\", \"Color : Blue/Brown\".
        *   *Images:* Clearly show a checked pattern (plaid). The dominant colors are brown tones and dark blue (almost black in some light).
        *   *Combine:* Describe the pattern as checked/plaid. State the colors as brown and blue. The text confirms \"Blue/Brown\". The images support this.
        *   *Result:* \"브라운과 네이비/블루 컬러의 체크 패턴\" (Brown and navy/blue colored check pattern).

    *   **`소재` (Material):**
        *   *Text:* \"체크 린넨 원단\", \"Material : Linen 100%\".
        *   *Images:* The fabric appears slightly textured and perhaps a bit sheer or lightweight, consistent with linen.
        *   *Combine:* Both text sources explicitly state Linen.
        *   *Result:* \"린넨 100%\" (Linen 100%).

    *   **`디테일` (Details):**
        *   *Text:* \"가먼트 워싱\", \"논카라 디테일\", \"아웃포켓 디테일\", \"밑단 올 풀림 디테일\", \"천연 자개 단추\".
        *   *Images:*
            *   Non-collar: Visible in the neck area, confirms \"논카라\".
            *   Out Pocket: Look closely at the chest area. Yes, there is a patch pocket on the left chest. Confirms \"아웃포켓\".
            *   Frayed Hem: Look at the bottom hem and cuffs. Yes, they have a distinct frayed, unfinished edge. Confirms \"밑단 올 풀림 디테일\".
            *   Buttons: Look at the buttons. They appear somewhat iridescent or have a natural variation in color, consistent with mother-of-pearl (자개). Confirms \"천연 자개 단추\".
            *   Garment Washing: This is a treatment that affects the feel and appearance, often giving a slightly worn or soft look. The images show a slightly faded or lived-in look, which could be consistent with garment washing, though it's harder to *see* explicitly than other details. However, the text lists it as a detail.
        *   *Combine:* List all the confirmed details from the text and images.
        *   *Result:* \"논카라, 아웃포켓, 밑단/소매 올 풀림, 천연 자개 단추, 가먼트 워싱\" (No collar, out pocket, hem/cuff frayed edges, natural mother-of-pearl buttons, garment washing). *Self-correction: The text says \"밑단 올 풀림\" but the images clearly show it on the cuffs too. Will include both hem and cuff in the description for accuracy based on the visual.*

    *   **`실루엣` (Silhouette):**
        *   *Text:* \"세미 오버 실루엣\".
        *   *Images:* The shirt fits loosely on the model, not tight, but not extremely oversized either. It has a relaxed, slightly baggy fit. This aligns with \"세미 오버\" (semi-oversized).
        *   *Combine:* Use the term from the text, as it matches the visual.
        *   *Result:* \"세미 오버 실루엣\" (Semi-oversized silhouette).

    *   **`분위기 및 지향점` (Mood and Aim):**
        *   *Text:* No explicit description of mood or aim, *but* the details (linen, frayed edges, garment washing, relaxed fit, check pattern) collectively suggest a certain style.
        *   *Images:* The overall look is casual, relaxed, perhaps slightly vintage or natural due to the fabric and frayed edges. The styling with jeans and sandals enhances this.
        *   *Combine:* Based on the material, details, and silhouette, deduce the intended mood/style. \"Natural,\" \"casual,\" \"relaxed,\" \"vintage-inspired\" could apply. Let's use terms that capture the essence of linen, relaxed fit, and the slightly aged look from washing and fraying.
        *   *Result:* \"내추럴하고 캐주얼하며 편안한 분위기\" (Natural, casual, and comfortable mood).

    *   **`세부 카테고리` (Detailed Category):**
        *   *Text:* \"Non Collar Linen French Check Shirt\". This is the specific product name. It includes key category information: \"Shirt\", \"Non Collar\", \"Linen\", \"Check\".
        *   *Images:* It's clearly a shirt, specifically a long-sleeved shirt. It has no traditional collar. It's made of linen and has a check pattern.
        *   *Combine:* Use the descriptive parts of the product name and observation from the images. It's a long-sleeved shirt with a specific type of collar (none) and pattern (check).
        *   *Result:* \"논카라 셔츠\" (Non-collar shirt) or \"체크 셔츠\" (Check shirt) or combine? \"린넨 체크 논카라 셔츠\" (Linen check non-collar shirt) is more specific. Let's go with a key identifying feature: \"논카라 셔츠\". Adding material and pattern might be too long for a simple category. Let's refine it to just the most prominent feature or standard category. \"셔츠\" is the base. \"논카라\" specifies it. \"체크\" is the pattern. \"린넨\" is the material. How specific should it be? The examples often lean towards type+key feature. \"논카라 셔츠\" seems appropriate. *Self-correction: Maybe \"체크 셔츠\" is a more common search term. Or \"린넨 셔츠\"? Let's list the most defining visual characteristics.* It's a *shirt*, it has *long sleeves*, it's *checked*, it's *collarless*. \"체크 린넨 셔츠\" captures material and pattern, and is a common category. \"논카라\" is a detail. Let's stick to a general category with key identifiers: \"체크 셔츠\". Or perhaps a more specific one combining type and pattern/material: \"남성 린넨 체크 셔츠\" (Men's linen check shirt)? The model is male, so \"남성\" is relevant. Yes, \"남성 린넨 체크 셔츠\" is quite specific and accurate.
        *   *Result:* \"남성 린넨 체크 셔츠\" (Men's linen check shirt).

4.  **Format as JSON:** Assemble the results into the specified JSON structure.

    ```json
    {
      \"색상 및 패턴\": \"브라운과 네이비/블루 컬러의 체크 패턴\",
      \"소재\": \"린넨 100%\",
      \"디테일\": \"논카라, 아웃포켓, 밑단/소매 올 풀림, 천연 자개 단추, 가먼트 워싱\",
      \"실루엣\": \"세미 오버 실루엣\",
      \"분위기 및 지향점\": \"내추럴하고 캐주얼하며 편안한 분위기\",
      \"세부 카테고리\": \"남성 린넨 체크 셔츠\"
    }
    ```

5.  **Final Review:**
    *   Does the JSON contain the required keys? Yes.
    *   Is the information based on both images and *relevant* text? Yes.
    *   Was irrelevant text ignored? Yes (Brand, Size info, model info, disclaimers).
    *   Does it focus on the shirt, not the whole outfit? Yes.
    *   Are the descriptions accurate based on the visuals and text? Yes.
    *   Is the output in JSON format? Yes.

The process seems complete and the resulting JSON fits the requirements."""
                    ),
                    types.Part.from_text(
                        text="""```json
{
  \"색상 및 패턴\": \"브라운과 네이비/블루 컬러의 체크 패턴\",
  \"소재\": \"린넨 100%\",
  \"디테일\": \"논카라, 아웃포켓, 밑단/소매 올 풀림, 천연 자개 단추, 가먼트 워싱\",
  \"실루엣\": \"세미 오버 실루엣\",
  \"분위기 및 지향점\": \"내추럴하고 캐주얼하며 편안한 분위기\",
   \"장르\" : \"캐주얼\",
  \"세부 카테고리\": \"셔츠\"
}
```"""
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.files[5].uri,
                        mime_type=self.files[5].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[6].uri,
                        mime_type=self.files[6].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[7].uri,
                        mime_type=self.files[7].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[8].uri,
                        mime_type=self.files[8].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[9].uri,
                        mime_type=self.files[9].mime_type,
                    ),
                    types.Part.from_text(
                        text="""MFPEN 은 2015년에 덴마크 코펜하겐을 베이스로 설립된 남성복 브랜드 입니다. 
북유럽 브랜드 답게 스칸디나비아 스타일 특유의 미니멀한 디자인의 의류가 주를 이루며
편안한 핏과 좋은 소재로 만들어진 제품들이 돋보이는 브랜드 입니다.

[Size & fit]
Relaxed fit. Model is 185 cm and wearing size medium.
Please see measurements on the last slide.

[Product details]
· Fabric made in Portugal
· Garment made in Portugal
· 100% Tencel®
· Garment washed
· Ivory resin buttons
· Machine wash cold"""
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""The user wants me to extract specific information about a piece of clothing from provided images and text and present it in a JSON format.

Here's the plan:
1.  **Analyze the request:**
    *   Input: Images of a garment and a rough description (text).
    *   Output: JSON format with specific keys: 색상 및 패턴, 소재, 디테일, 실루엣, 분위기 및 지향점, 세부 카테고리.
    *   Constraint 1: Ignore irrelevant text (brand history, care instructions, sizing table details, model size info). Focus on garment features (fabric, details, silhouette, atmosphere, intention).
    *   Constraint 2: Look at the images and text. If the image shows a full outfit, focus only on the *shirt* based on the text description (which describes a shirt). Use the image to identify color, pattern, and visible details/silhouette. Combine image and text info.

2.  **Examine the input:**
    *   **Images:** Show a light blue shirt with dark vertical stripes, worn by a model. The shirt has a collar, button front, and a single chest pocket. The model also wears black pants, but the request specifies focusing on the shirt.
    *   **Text:**
        *   Brand info (MFPEN, Copenhagen, Scandinavian style, minimal design, comfortable fit, good material) - *Ignore brand history/philosophy details, but 'minimal design', 'comfortable fit', 'good material' might contribute to atmosphere/silhouette/material sections.*
        *   Size & fit (Relaxed fit, model info, link to measurements) - *Use 'Relaxed fit' for Silhouette. Ignore model info and measurement table.*
        *   Product details (Fabric/Garment origin, 100% Tencel®, Garment washed, Ivory resin buttons, Machine wash cold) - *Use '100% Tencel®' for 소재. Use 'Garment washed' and 'Ivory resin buttons' for 디테일. Ignore origin and wash instructions.*
        *   Product name: Executive Shirt - Arona Blue - *Confirms it's a shirt and provides color name.*

3.  **Synthesize the information for each JSON key:**
    *   **색상 및 패턴:** Images show light blue with dark vertical stripes. Text mentions \"Arona Blue\". So, \"라이트 블루 바탕에 짙은 세로 스트라이프 패턴\" (Light blue base with dark vertical stripe pattern) or similar.
    *   **소재:** Text explicitly states \"100% Tencel®\". So, \"텐셀 100%\".
    *   **디테일:** Images show a collar, button front, chest pocket. Text mentions \"Garment washed\" and \"Ivory resin buttons\". So, \"버튼 프론트, 싱글 체스트 포켓, 가먼트 워싱, 아이보리 레진 단추\" (Button front, single chest pocket, garment washed, ivory resin buttons).
    *   **실루엣:** Text explicitly states \"Relaxed fit\". Images also show a relaxed, slightly oversized fit. So, \"릴렉스 핏\".
    *   **분위기 및 지향점:** Text mentions \"minimal design\", \"comfortable fit\", \"good material\", \"Scandinavian style\". Images show a clean, relaxed look. This suggests a \"미니멀하고 편안한, 캐주얼한\" (Minimal, comfortable, casual) or similar vibe. Let's combine aspects like minimal, comfortable, relaxed, perhaps with a hint of sophistication from \"Executive Shirt\". \"미니멀하며 편안한 캐주얼 셔츠의 분위기\" (Atmosphere of a minimal and comfortable casual shirt).
    *   **세부 카테고리:** Images and text clearly describe a \"Shirt\". So, \"셔츠\".

4.  **Construct the JSON:** Assemble the synthesized information into the specified JSON structure."""
                    ),
                    types.Part.from_text(
                        text="""```json
{
  \"색상 및 패턴\": \"라이트 블루 바탕에 짙은 세로 스트라이프 패턴\",
  \"소재\": \"텐셀 100%\",
  \"디테일\": \"레귤러 칼라, 버튼 프론트, 싱글 체스트 포켓, 가먼트 워싱, 아이보리 레진 단추\",
  \"실루엣\": \"릴렉스 핏\",
  \"분위기 및 지향점\": \"미니멀하고 편안한 캐주얼 분위기\",
  \"장르\" : \"미니멀, 캐주얼\",
  \"세부 카테고리\": \"셔츠\"
}
```"""
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.files[10].uri,
                        mime_type=self.files[10].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[11].uri,
                        mime_type=self.files[11].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[12].uri,
                        mime_type=self.files[12].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[13].uri,
                        mime_type=self.files[13].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[14].uri,
                        mime_type=self.files[14].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[15].uri,
                        mime_type=self.files[15].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[16].uri,
                        mime_type=self.files[16].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[17].uri,
                        mime_type=self.files[17].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[18].uri,
                        mime_type=self.files[18].mime_type,
                    ),
                    types.Part.from_text(
                        text="""제품명 : BK Cigar co. Heavyweight Tee Off White

BK Cigar co. Heavyweight Tee


감독 웨인왕과 소설가 폴오스터가 만든 영화 [스모크]의 배경인 가상의 담배가게 '브루클린 시가샵'의 그래픽이 새겨진 헤비웨이트 티셔츠


SPECIFICATION


- Outer Fabric - Cotton 100%

- Silk Screen Printing

- Ribbed Crew Neck Detail

- One Washed


탄탄한 내구성과 균일한 조직감을 지닌 OE + CD 10's 원사로 제작된 에스피오나지의 헤비웨이트 티셔츠 고중량 원단 특유의 견고함에 덴타 덤블 가공을 거쳐 세탁후에도 변형과 수축을 회소화하고 더욱 안정적인 실루엣을 완성했습니다 기존보다 한층 부드러워진 텍스처로 편안한 착용감을 더한 에스피오나지의 헤비 웨이트 티셔츠를 직접 경험해보세요 """
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""The user wants to extract key information about a t-shirt from images and provided text description and format it as a JSON object.

Here's the plan:
1.  Analyze the images: Identify the main garment (t-shirt), its color, pattern (if any), and silhouette. Note the graphic print.
2.  Analyze the text description: Extract relevant information about the garment, ignoring brand history, fit advice, and care instructions unless they describe a specific *feature* of the garment (like 'garment washed' which affects the texture/feel/color). Focus on:
    *   Color/Pattern: \"Off White\", \"BK Cigar co. Heavyweight Tee\", \"가상의 담배가게 '브루클린 시가샵'의 그래픽\" (Graphic print).
    *   Material: \"Cotton 100%\", \"OE + CD 10's 원사\", \"고중량 원단\" (Heavyweight fabric).
    *   Details: \"Silk Screen Printing\", \"Ribbed Crew Neck Detail\", \"One Washed\", \"덴타 덤블 가공\" (Tenta Dumble processing for minimal shrinkage/변형). The graphic is a key detail.
    *   Silhouette: The text mentions \"안정적인 실루엣\" (stable silhouette) due to processing, and the images show a slightly relaxed/standard fit.
    *   Atmosphere/Intention: \"감독 웨인왕과 소설가 폴오스터가 만든 영화 [스모크]의 배경인 가상의 담배가게 '브루클린 시가샵'의 그래픽\" indicates a vintage/cinematic/story-driven theme. \"헤비웨이트 티셔츠\" implies durability and solid structure.
    *   Sub Category: T-shirt.
3.  Combine image and text information: Ensure the description aligns with what's visible in the images. The images show two t-shirts, one white and one dark gray. The text is for the \"Off White\" version. Focus on the white one as it's the primary subject and described. The dark gray one is just for reference (back print example).
4.  Map the extracted information to the required JSON keys:
    *   색상 및 패턴: Off White color, graphic print on front and back. Describe the graphic content (\"Brooklyn Cigar Co.\", address, items listed, Espionage logo).
    *   소재: Cotton 100%, Heavyweight fabric (고중량), OE + CD 10's yarn.
    *   디테일: Graphic silk screen printing, Ribbed crew neck, One washed, Tenta Dumble processed (for stability), front and back print.
    *   실루엣: Seems like a standard fit based on the image, maybe slightly relaxed due to \"Heavyweight\". \"안정적인 실루엣\" implies structure.
    *   분위기 및 지향점: Vintage/cinematic inspired (from movie reference), durable, solid, casual.
    *   세부 카테고리: 티셔츠.
5.  Refine the descriptions for clarity and conciseness, using Korean terms provided where appropriate.
6.  Format as JSON.

Reviewing the text:
- Brand/Movie reference: Keep the movie reference as it explains the *graphic* detail, which is relevant to the garment itself (its print). Ignore the brand history beyond that.
- Material details: \"Cotton 100%\", \"OE + CD 10's 원사\", \"고중량 원단\" are all material properties.
- Processing details: \"Silk Screen Printing\", \"One Washed\", \"덴타 덤블 가공\" are finishing details affecting the final product. These are relevant.
- Fit/Silhouette: \"탄탄한 내구성과 균일한 조직감\", \"고중량 원단 특유의 견고함\", \"안정적인 실루엣\", \"부드러워진 텍스처\", \"편안한 착용감\" - these describe the feel and structure, contributing to the silhouette/feel.

Revised mapping:
*   색상 및 패턴: 오프 화이트 색상, 전면 및 후면 그래픽 프린팅. (그래픽 내용 추가)
*   소재: 코튼 100%, 고중량 헤비웨이트 원단 (OE + CD 10수 원사)
*   디테일: 실크 스크린 프린팅 (전면 'Brooklyn Cigar Co.' 로고, 후면 주소 및 항목, Espionage 로고), 립넥 디테일, 원 워싱, 덴타 덤블 가공
*   실루엣: 안정적이고 견고한 실루엣 (고중량 원단 및 가공 특성 반영)
*   분위기 및 지향점: 영화 '스모크'에서 영감받은 그래픽 디자인, 캐주얼하고 빈티지한 무드, 탄탄하고 내구성 있는 착용감.
*   세부 카테고리: 티셔츠

Looks good. Proceed with generating the JSON."""
                    ),
                    types.Part.from_text(
                        text="""```json
{
  \"색상 및 패턴\": \"오프 화이트 색상, 전면 및 후면에 레드/화이트 그래픽 프린팅\",
  \"소재\": \"코튼 100%, 고중량 헤비웨이트 원단 (OE + CD 10수 원사 사용)\",
  \"디테일\": \"전면 가슴 중앙에 글자 프린팅, 후면 전반에 글자 프린팅, 브랜드 로고 실크 스크린 프린팅, 립넥 디테일, 원 워싱, 덴타 덤블 가공 (변형/수축 최소화)\",
  \"실루엣\": \"안정적이고 견고한 실루엣\",
  \"분위기 및 지향점\": \"영화에서 영감받은 그래픽 디자인, 캐주얼하고 빈티지한 무드, 탄탄하고 내구성 있는 착용감\",
   \"장르\" : \"아메리칸 캐주얼\",
  \"세부 카테고리\": \"티셔츠\"
}
```"""
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.files[19].uri,
                        mime_type=self.files[19].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[20].uri,
                        mime_type=self.files[20].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[21].uri,
                        mime_type=self.files[21].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[22].uri,
                        mime_type=self.files[22].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[23].uri,
                        mime_type=self.files[23].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[24].uri,
                        mime_type=self.files[24].mime_type,
                    ),
                    types.Part.from_text(
                        text="""Smoking Rat(Peeing) Heavyweight Tee


90년대 미국에서 유행했던 \"Peeing Calvin\"을 패러디한 스모킹 랫 캐릭터와 흡연에 대한 자조적인 문구가 새겨진 헤비웨이트 티셔츠


SPECIFICATION


- Outer Fabric - Cotton 100%

- Silk Screen Printing

- Ribbed Crew Neck Detail

- One Washed


탄탄한 내구성과 균일한 조직감을 지닌 OE + CD 10's 원사로 제작된 에스피오나지의 헤비웨이트 티셔츠 고중량 원단 특유의 견고함에 덴타 덤블 가공을 거쳐 세탁후에도 변형과 수축을 회소화하고 더욱 안정적인 실루엣을 완성했습니다 기존보다 한층 부드러워진 텍스처로 편안한 착용감을 더한 에스피오나지의 헤비 웨이트 티셔츠를 직접 경험해보세요"""
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""Thinking Process:

1.  **Identify the Goal:** The user wants a JSON output describing a piece of clothing based on provided images and text descriptions. The JSON should contain specific keys: \"색상 및 패턴\", \"소재\", \"디테일\", \"실루엣\", \"분위기 및 지향점\", \"세부 카테고리\". I need to ignore irrelevant information (brand name, washing instructions, size charts, model info, disclaimers) and focus *only* on the characteristics of the garment itself, combining information from both the text and the images. I also need to prioritize the specific garment shown in the images (the white tee) even if the description mentions a different color variant (yellow).

2.  **Analyze the Input:**
    *   **Images:** Show a white t-shirt with a graphic print on the front chest and a larger graphic print on the back. The print is a cartoon rat smoking, with text around it. Another image shows a yellow version of the same tee, and one shows a model wearing the white tee with shorts. The key is the *white* tee shown in most images.
    *   **Text:**
        *   Product Name: \"Smoking Rat(Peeing) Heavyweight Tee\" (implies a graphic tee, heavyweight).
        *   Description: Refers to a \"Smoking Rat\" character parodied from \"Peeing Calvin\". Mentions a \"자조적인 문구 (sarcastic phrase)\" about smoking.
        *   Specification:
            *   Fabric: \"Cotton 100%\"
            *   Printing: \"Silk Screen Printing\"
            *   Neck: \"Ribbed Crew Neck Detail\"
            *   Wash: \"One Washed\"
            *   Fabric details: \"탄탄한 내구성과 균일한 조직감을 지닌 OE + CD 10's 원사\", \"고중량 원단 특유의 견고함\", \"덴타 덤블 가공을 거쳐 세탁후에도 변형과 수축을 회소화하고 더욱 안정적인 실루엣\", \"한층 부드러워진 텍스처로 편안한 착용감\". These describe the *material* and the resulting *feel/durability/silhouette*.

3.  **Map Information to JSON Keys:**

    *   **색상 및 패턴 (Color and Pattern):**
        *   Images show: White t-shirt. Black outline graphic print on front and back. Text print in black on front and back.
        *   Text mentions: \"Smoking Rat(Peeing) Heavyweight Tee\", \"스모킹 랫 캐릭터\", \"자조적인 문구\". Product name mentions \"Off White\".
        *   Combine: Off-white base color. Graphic print of a smoking rat character. Text print.
        *   Result: 오프 화이트 색상. 흡연하는 쥐 캐릭터 및 문구 그래픽 프린팅.

    *   **소재 (Material):**
        *   Text mentions: \"Cotton 100%\", \"Heavyweight Tee\", \"OE + CD 10's 원사\", \"고중량 원단\", \"탄탄한 내구성\", \"균일한 조직감\", \"부드러워진 텍스처\".
        *   Combine: Cotton 100%. Heavyweight fabric (고중량). OE + CD 10수 원사. Descriptors: durable (탄탄한 내구성), even texture (균일한 조직감), soft texture (부드러워진 텍스처).
        *   Result: 코튼 100%, 고중량 헤비웨이트 원단 (OE + CD 10수 원사 사용), 탄탄하고 부드러운 텍스처

    *   **디테일 (Details):**
        *   Images show: Crew neck. Print on front and back.
        *   Text mentions: \"Silk Screen Printing\", \"Ribbed Crew Neck Detail\", \"One Washed\", \"덴타 덤블 가공\". Mentions graphic character and text.
        *   Combine: Graphic print (실크 스크린 프린팅) of the character and text. Ribbed crew neck. One-washed. Denta tumble finishing (덴타 덤블 가공).
        *   Result: 라운드넥 (립넥), 전면 및 후면 실크 스크린 그래픽/문구 프린팅, 원 워싱, 덴타 덤블 가공

    *   **실루엣 (Silhouette):**
        *   Images show: Appears slightly oversized or relaxed fit on the model. Standard t-shirt shape.
        *   Text mentions: \"Heavyweight Tee\", \"안정적인 실루엣\" (resulting from finishing).
        *   Combine: Heavyweight implies a solid structure. The images suggest a standard or slightly relaxed t-shirt fit. \"안정적인 실루엣\" reinforces a non-clingy shape.
        *   Result: 안정적이고 견고한 실루엣, 일반적인 티셔츠 핏 (이미지상 살짝 여유로워 보임) -> Let's stick to the text description's \"안정적이고 견고한 실루엣\" and the overall look in the image. \"Heavyweight Tee\" often implies a boxier/structured fit.
        *   Refined Result: 안정적이고 견고한 실루엣, 헤비웨이트 원단 특유의 형태감

    *   **분위기 및 지향점 (Atmosphere and Aim):**
        *   Text mentions: Parody (패러디), sarcastic phrase (자조적인 문구), 90s American trend (90년대 미국에서 유행). Durable/comfortable fabric.
        *   Combine: Playful/humorous graphic (parody, character). Sarcastic/irreverent tone (text). References 90s pop culture. Focus on comfort and durability.
        *   Result: 유머러스하고 캐주얼한 분위기, 90년대 트렌드 패러디, 편안하고 내구성 있는 착용감

    *   **세부 카테고리 (Detailed Category):**
        *   Text mentions: \"Heavyweight Tee\", \"티셔츠\".
        *   Result: 티셔츠

4.  **Construct the JSON:** Assemble the results into the specified JSON format.

5.  **Review and Refine:** Read through the generated JSON and compare it against the input (images and text) and the user's requirements (ignore irrelevant info, focus on the garment, combine info).
    *   Color/Pattern: Correctly captures the white base and graphic.
    *   Material: Correctly captures cotton 100%, heavyweight, and finishing details relevant to material feel/durability.
    *   Details: Correctly lists neck, printing, and finishing processes.
    *   Silhouette: \"안정적이고 견고한 실루엣\" from text fits well.
    *   Atmosphere: Captures the graphic's tone and inspiration, plus the comfort/durability aspect.
    *   Category: Correctly identified as a t-shirt.
    *   Irrelevant info check: Brand, wash instructions (beyond 'one washed'), size chart, model info, disclaimers were ignored. Focus is on the garment itself.

The JSON seems accurate and adheres to the user's instructions."""
                    ),
                    types.Part.from_text(
                        text="""```json
{
  \"색상 및 패턴\": \"오프 화이트 색상, 흡연하는 쥐 캐릭터 및 문구 그래픽 프린팅 (블랙)\",
  \"소재\": \"코튼 100%, 고중량 헤비웨이트 원단 (OE + CD 10수 원사 사용), 탄탄하고 부드러운 텍스처\",
  \"디테일\": \"립 라운드넥, 전면 가슴 왼편에 캐릭터 그래픽 실크 프린팅  후면 전반에 캐릭터 및 문구 실크 스크린 그래픽/ 문구 프린팅, 원 워싱, 덴타 덤블 가공\",
  \"실루엣\": \"안정적이고 견고한 실루엣, 헤비웨이트 원단 특유의 형태감\",
  \"분위기 및 지향점\": \"유머러스하고 캐주얼한 분위기, 90년대 트렌드 패러디, 편안하고 내구성 있는 착용감\",
  \"장르\" : \"아메리칸 캐주얼\",
  \"세부 카테고리\": \"티셔츠\"
}
```"""
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.files[25].uri,
                        mime_type=self.files[25].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[26].uri,
                        mime_type=self.files[26].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[27].uri,
                        mime_type=self.files[27].mime_type,
                    ),
                    types.Part.from_uri(
                        file_uri=self.files[28].uri,
                        mime_type=self.files[28].mime_type,
                    ),
                    types.Part.from_text(
                        text="""제품명 : 멘즈 토렌트쉘 3L 레인 재킷 / 85241P7
    토렌트쉘 3L 재킷은 심플한 디자인과 파타고니아의 고기능성 H2NO® 퍼포먼스 스탠더드 기술이 만나 뛰어난 방수/투습성을 자랑하는 제품입니다. 토렌트쉘은 하루 종일 착용해도 편안하며, 방수 내구성이 오랫동안 지속됩니다. 3레이어로 된 쉘은 PFC-free 처리(원단, 멤브레인 및 마감재에 과불화화합물이 들어있지 않음)가 되어 있습니다.
    100% 리사이클 방수/투습 겉감

    방수/투습성이 뛰어난 3레이어 H2No® 퍼포먼스 스탠더드 쉘 원단을 사용하였으며, PFC-free DWR 처리(원단, 멤브레인 및 내구성 발수처리 마감재에도 과불화화합물이 들어있지 않지 않음)가 되어 있어, 최적의 편안함과 고기능성을 자랑하는 제품입니다. 방수와 내구성이 장기간 유지됩니다.

    사이즈 조절이 가능한 후드

    후드에는 래미네이트 처리한 챙이 있습니다. 후드는 양쪽에서 조임끈을 당겨 조일 수 있고 사용하지 않을 때는 접어서 뒷부분의 벨크로로 고정할 수 있습니다.

    마이크로플리스 안감을 사용한 목

    목 뒤쪽에 덧댄 마이크로 플리스는 피부에 닿는 느낌을 부드럽게 하고 멤브레인을 보호합니다.

    전면 중앙 지퍼

    가운데 지퍼 안쪽과 바깥쪽에는 지퍼 바람막이가 있으며 지퍼 손잡이가 턱에 닿는 것을 방지하는 지퍼집이 있습니다.

    주머니 특징

    양쪽에 손 주머니가 있으며, 통기성을 위해 겨드랑이에도 지퍼가 달려있습니다.

    뛰어난 보온성

    손목 부분은 벨크로로 조입니다. 허리 조임끈이 있습니다.

    생산 노동자 지원

    생산 노동자들의 생활 개선을 위해 지원금을 공정 무역 노동자 위원회에 직접 지급하는 공정 무역 (Fair Trade Certified™) 봉제 제품입니다.

    무게

    400g

    소재

    PFC-free H2No® 퍼포먼스 스탠다드 쉘(원단부터 멤브레인, 발수 가공 공정에 이르기까지 과불화화합물이 들어있지 않음): 3레이어, 94g 50데니어 에코닐(ECONYL®) 100% 리사이클 나일론 립스탑 겉감, 바이오베이스가 13% 함유된 폴리카보네이트 PU 멤브레인, 트리코트 배커와 PFC-free DWR 처리(과불화화합물이 들어있지 않은 내구성 발수 처리)

    원단은 블루사인(bluesign®) 인증 원단"""
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="""Here's my thinking process to arrive at the desired JSON output based on the user's request:

    1.  **Understand the Goal:** The user wants a JSON object describing a piece of clothing based on provided images and text description. The description should focus *only* on the garment itself (color, detail, silhouette, material, mood, category, genre) and ignore irrelevant information like brand history, washing instructions, or sizing charts (beyond how fit is described). The images should inform aspects like color, silhouette, and visible details. The output must be in a specific JSON format with predefined keys and a controlled vocabulary for the \"장르\" field.

    2.  **Identify the Garment:** The images show a hooded jacket. The text describes it as a \"멘즈 토렌트쉘 3L 레인 재킷\". This confirms it's a jacket, specifically a rain jacket.

    3.  **Process the Text Description:** I'll go through the provided text section by section and extract relevant information, discarding irrelevant parts.

        *   `제품명 : 멘즈 토렌트쉘 3L 레인 재킷 / 85241P7`: Useful for the \"세부 카테고리\". It's a rain jacket.
        *   `토렌트쉘 3L 재킷은 심플한 디자인과 파타고니아의 고기능성 H2NO® 퍼포먼스 스탠더드 기술이 만나 뛰어난 방수/투습성을 자랑하는 제품입니다. 토렌트쉘은 하루 종일 착용해도 편안하며, 방수 내구성이 오랫동안 지속됩니다.`: Mentions \"심플한 디자인\", \"고기능성\", \"방수/투습성\", \"편안함\", \"내구성\". This is useful for \"분위기 및 지향점\" and \"소재\" (implicitly, related to performance).
        *   `3레이어로 된 쉘은 PFC-free 처리(...)가 되어 있습니다.`: Relates to \"소재\" and \"디테일\" (specifically, the treatment).
        *   `100% 리사이클 방수/투습 겉감`: Material composition and function. Goes to \"소재\".
        *   `방수/투습성이 뛰어난 3레이어 H2No® 퍼포먼스 스탠더드 쉘 원단을 사용하였으며, PFC-free DWR 처리(...)가 되어 있어, 최적의 편안함과 고기능성을 자랑하는 제품입니다. 방수와 내구성이 장기간 유지됩니다.`: Reinforces material, performance (방수/투습/내구성/편안함/고기능성), and PFC-free DWR treatment. Goes to \"소재\" and \"분위기 및 지향점\".
        *   `사이즈 조절이 가능한 후드`: A \"디테일\".
        *   `후드에는 래미네이트 처리한 챙이 있습니다.`: A \"디테일\" of the hood.
        *   `후드는 양쪽에서 조임끈을 당겨 조일 수 있고 사용하지 않을 때는 접어서 뒷부분의 벨크로로 고정할 수 있습니다.`: More \"디테일\" about the hood (drawstring, velcro).
        *   `마이크로플리스 안감을 사용한 목`: A \"소재\" detail and \"디테일\" about the collar area.
        *   `목 뒤쪽에 덧댄 마이크로 플리스는 피부에 닿는 느낌을 부드럽게 하고 멤브레인을 보호합니다.`: Explains the function/feel, contributing to \"소재\", \"디테일\", and \"분위기 및 지향점\" (comfort).
        *   `전면 중앙 지퍼`: A \"디테일\".
        *   `가운데 지퍼 안쪽과 바깥쪽에는 지퍼 바람막이가 있으며 지퍼 손잡이가 턱에 닿는 것을 방지하는 지퍼집이 있습니다.`: More \"디테일\" about the zipper (storm flap, chin guard).
        *   `주머니 특징`: Introduces pocket details.
        *   `양쪽에 손 주머니가 있으며, 통기성을 위해 겨드랑이에도 지퍼가 달려있습니다.`: \"디테일\" - hand pockets and pit zips (ventilation).
        *   `뛰어난 보온성`: This is a bit ambiguous for a rain shell, but the previous text mentioned comfort and membrane protection. I'll consider if this fits \"분위기 및 지향점\" (intended function in various weather).
        *   `손목 부분은 벨크로로 조입니다. 허리 조임끈이 있습니다.`: More \"디테일\" (velcro cuffs, waist drawstring).
        *   `생산 노동자 지원... 공정 무역 봉제 제품입니다.`: Irrelevant (brand/ethical detail, not garment feature).
        *   `무게 400g`: Irrelevant (specific spec, not general description).
        *   `소재 PFC-free H2No® 퍼포먼스 스탠다드 쉘(...) 3레이어, 94g 50데니어 에코닐(ECONYL®) 100% 리사이클 나일론 립스탑 겉감, 바이오베이스가 13% 함유된 폴리카보네이트 PU 멤브레인, 트리코트 배커와 PFC-free DWR 처리(...)`: Detailed material breakdown. Key parts are 3-layer H2No, 100% recycled nylon ripstop, PFC-free DWR. The technical terms like '94g 50데니어', '폴리카보네이트 PU 멤브레인', '트리코트 배커', 'ECONYL®' might be too specific unless simplified. I'll focus on the main aspects: 3-layer, recycled nylon ripstop, H2No, PFC-free DWR.
        *   `원단은 블루사인(bluesign®) 인증 원단`: Irrelevant (certification, not garment feature).

    4.  **Process the Images:**
        *   Look at the jacket in different colors (black, tan, green, brown). The user only needs *a* representative color/pattern, or a list if multiple are shown *on the garment itself*. Since the images show the *same* jacket in different colors, I should list the colors visible. The primary focus is on the garment, so listing the presented color options is appropriate. Colors are black, tan, green, dark brown/grey. There's no pattern visible on the main fabric.
        *   Observe the silhouette: It appears to be a regular fit, perhaps slightly relaxed, suitable for layering or movement. Not overly baggy or tight. It has a standard jacket length.
        *   Look for visible details not explicitly mentioned or to confirm mentioned ones: Hood, full zip front, hand pockets (zippered, likely hidden or integrated), pit zips (visible zippers under the arms), adjustable cuffs (velcro visible), adjustable hem (drawstring implied by text). There's a small Patagonia logo on the chest.

    5.  **Synthesize and Populate JSON Fields:**

        *   **색상 및 패턴:** The images show solid colors. List the colors: 블랙, 탄, 그린, 다크 브라운/그레이.
        *   **소재:** From text: 100% 리사이클 나일론 립스탑 겉감, 3레이어 H2No® 퍼포먼스 스탠다드 쉘, PFC-free DWR 처리. Also mention the microfleece lining at the neck.
        *   **디테일:** From text and image: 조절 가능한 후드 (챙 있음, 조임끈, 벨크로 고정), 마이크로플리스 넥 안감, 전면 중앙 지퍼 (바람막이, 지퍼집), 지퍼형 손 주머니, 겨드랑이 통기 지퍼, 벨크로 소매 조절, 밑단 조임끈, 파타고니아 로고 패치.
        *   **실루엣:** From image and text (implicitly, \"하루 종일 착용해도 편안하며...안정적인 실루엣\"): 레귤러 핏, 활동에 용이한 형태. \"심플한 디자인\"도 실루엣과 관련될 수 있음.
        *   **분위기 및 지향점:** From text: 고기능성 (방수/투습/내구), 편안함, 아웃도어 활동 적합, 심플함. From brand identity (implied by Patagonia): 환경 친화적 (리사이클 소재, PFC-free), 기능성, 실용성. Combine these: 기능성 아웃도어, 심플하고 실용적, 환경 친화적 지향.
        *   **장르:** The garment is clearly an outdoor rain jacket from Patagonia. The primary genre is \"아웃도어\". It's also a functional piece that fits well into \"캐주얼\" wear. Given the explicit technical features and brand, \"아웃도어\" is the most prominent. I'll put \"아웃도어\" first, followed by \"캐주얼\".
        *   **세부 카테고리:** From product name and images: 레인 재킷, 후드 재킷. \"재킷\"으로 포괄해도 되지만 \"레인 재킷\"이 더 구체적. \"후드 재킷\"도 가능. \"레인 재킷\"이 가장 정확하다.

    6.  **Review and Refine:** Read through the generated descriptions for each key. Ensure they are concise, directly relevant to the garment's appearance and stated features (excluding brand/care/sizing details), and flow well. Check against the images to confirm visual aspects. Ensure the JSON format is correct.

        *   색상 및 패턴: List the visible color options. OK.
        *   소재: Summarize the key technical materials and treatments. OK.
        *   디테일: List the functional and design features. OK.
        *   실루엣: Describe the general fit and shape. OK.
        *   분위기 및 지향점: Capture the intended use and aesthetic/functional goals. OK.
        *   장르: Select from the list. \"아웃도어\" and \"캐주얼\" seem appropriate. Prioritize \"아웃도어\". OK.
        *   세부 카테고리: Identify the specific type of garment. \"레인 재킷\". OK.

    7.  **Final JSON Construction:** Assemble the refined descriptions into the final JSON structure.

    This thought process systematically extracts and filters information, combining text details with visual observation to create a structured description according to the user's specified criteria and format."""
                    ),
                    types.Part.from_text(
                        text="""```json
    {
    \"색상 및 패턴\": \"블랙, 탄, 그린, 다크 브라운/그레이 등 다양한 단색\",
    \"소재\": \"100% 리사이클 나일론 립스탑 겉감, 폴리카보네이트 PU 멤브레인, 트리코트 배커) 마이크로플리스 넥 안감\",
    \"디테일\": \"조절 가능한 후드 (래미네이트 챙, 조임끈, 벨크로 고정), 전면 중앙 지퍼 (바람막이, 지퍼집), 지퍼형 손 주머니, 겨드랑이 통기 지퍼, 벨크로 소매 조절, 밑단 조임끈, 브랜드 로고 패치\",
    \"실루엣\": \"심플하고 활동에 용이한 레귤러 핏\",
    \"분위기 및 지향점\": \"고기능성 (방수, 투습, 내구), 실용적, 아웃도어 활동 적합, 환경 친화적 지향\",
    \"장르\" : \"아웃도어\",
    \"세부 카테고리\": \"레인 재킷\"
    }
    ```"""
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=parts,  # my parts
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            # response_mime_type="text/plain",
            response_mime_type="application/json",
            system_instruction=[
                types.Part.from_text(
                    text="""옷의 이미지, 그리고 옷에 대한 러프한 설명을 입력으로 줄거야
    나의 목적은 다음과 같아 옷 자체에 대한 설명(색감, 디테일, 실루엣, 소재, 분위기)를 json형태로 key별로 뽑아서 가지고싶어 이걸 이용해서 text embedding을해서 searching 기능을 낼거야. 그래서 답변은 Json 양식으로 줘
    너는 2가지를 해야해 
    1. 옷에 대한 설명 중 불필요한 설명은 무시해. 여기서 불필요한 설명이랑 옷 자체에 대한 내용이 아닌 브랜드에 대한 설명, 세탁에 대한 설명, 주의사항에 대한 설명 등이야. 이런 정보를 무시하고 옷과 직접적으로 관련이 있는 정보 옷에 대해서 사용자가 참고할 만한 설명 (소재, 디테일, 분위기, 의도 )만 집중해서 정리해서 나에게 뱉어줘
    2.  옷에 대한 이미지를 보고 옷에 대표되는 색감, 디테일, 실루엣 , 분위기, 상세 카테고리를 위의 정보와 합쳐서 json 형태로 뱉어줘 이때 중요한건 보낸 이미지들 중에서 옷만 있는게 아니라 옷을 입고 있는 사람의 착장이나 옷과 관련없는 이미지가 들어갈 수 있어 너가 집중해야하는건 보낸 이미지들 중에서 옷들에 집중하는거야 상하의 착장이 같이 있어도 옷에 대한 설명, 이미지들을 봤을때 그게 상의라면 상의에 대해서만 묘사해

    장르는 다음 중 하나로 뱉어줘 만약에 이중에 해당하지 않으면 null을 내보내고 복수로 해당되면 복수를 ,로 구분해서 저장하는데, 가장 근사한 애의 순서대로 나열해 가령 아메리칸 캐주얼과 아메카지 둘다 해당되는 것 같을땐 그 중 더 확실한애를 앞에 둬
    - 캐주얼
    - 아메리칸 캐주얼
    - 아메카지
    - 스트릿
    - 댄디
    - 미니멀리즘
    - 클래식 
    - 워크웨어 
    - 프레피 
    - 락시크
    - 아웃도어

    대답은 json으로 뱉고 항목은 다음과 같아

    색상 및 패턴 :
    소재 : 
    디테일 :
    실루엣 : 
    분위기  및 지향점 :
    장르 : 
    세부 카테고리 : 
    """
                ),
            ],
        )

        response = ""

        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response += chunk.text
        # JSON 파싱 및 카테고리 추출
        json_response = json.loads(response)
        return json_response


if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent
    from dotenv import load_dotenv

    load_dotenv()
    prompt_dir = BASE_DIR.parent / "prompt_images"  # 예: main에서 한 단계 위로
    # for tmp_file in Path(prompt_dir).glob("*"):
    #     print(tmp_file)

    example_images = BASE_DIR.parent / "example_images"
    images = [
        Image.open(example_image).convert("RGB")
        for example_image in Path(example_images).glob("*")
    ]

    analyzer = Analyzer()
    json_response = analyzer.analyze(images=images, description="blue wool shirt")
    print(json_response)

    json_response = analyzer.analyze(images=images, description="blue wool shirt")
    print(json_response)
