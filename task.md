### TASK
WE WANTY TO USE NANO BADNANA 2 to generate one image for each of the images belonging to each and every single chair!! Plan then test one three images, then well do all after that. all on 1x1 aspect ratio 1000px at start., using prompt as this; "place it sharp against solid white background, have the  subject cut sharply, and bacground be #fff 100% white. " ALong with the image

# To run this code you need to install the following dependencies:
# pip install google-genai

import mimetypes
import os
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-3.1-flash-image-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""ace it sharp against solid white background, have the  subject cut sharply, and bacground be #fff 100% white."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="MINIMAL",
        ),
        image_config = types.ImageConfig(
            aspect_ratio="1:1",
            image_size="1K",
            person_generation="",
        ),
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
    )

    file_index = 0
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.parts is None
        ):
            continue
        if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
            file_name = f"ENTER_FILE_NAME_{file_index}"
            file_index += 1
            inline_data = chunk.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)

if __name__ == "__main__":
    generate()


