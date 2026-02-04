from PIL import Image
from qwen_vl_utils import process_vision_info
import time


def query_local(model, processor, device, image: Image.Image, question: str):
    start_time = time.time()
    print("starting local inference at: %s" % (start_time))
    if not image:
        raise ValueError("Missing image")

    # Math Tutor Prompt Engineering
    system_prompt = "You are a patient and helpful math tutor. Help the student solve the math problem shown in the image. Show your work step-by-step."
    full_prompt = f"{system_prompt}\n\nQuestion: {question}"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": full_prompt},
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    images, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=text, images=images, videos=video_inputs, padding=True, return_tensors="pt"
    )

    inputs = inputs.to(device)

    generated_ids = model.generate(**inputs, max_new_tokens=512)

    print("inputs generated")
    generated_ids_trimmed = [
        out_ids[len(in_ids) :]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    print("trimmed")

    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )

    print("decoded")

    print("local %s --- " % (time.time() - start_time))

    return output_text[0]
