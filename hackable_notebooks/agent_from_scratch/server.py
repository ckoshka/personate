from quart import Quart, render_template, websocket, request, send_from_directory, make_response, Response
app = Quart(__name__)
import asyncio
from hackable_notebooks.agent_from_scratch.dialogue_generator import generate_dialogue
from quart_cors import route_cors
@app.post("/")
@route_cors(allow_origin="*")
async def handle_post():
    data = await request.get_json(force=True)
    print(data)
    conversation = data["conversation"]
    response = await generate_dialogue(
        "Chair",
        "Pretend to be an IKEA Lerhamn Chair, black-brown, Vittaryd beige",
        is_ai=True,
        conversation=conversation,
        examples=["""<Human> whats it like being a chair?\n<Chair> What's it like not being a chair? You have a Cartesian coordinate-system whose spatiality admits only human forms, I am a plush chaise longue, the upholstery for your backside. I exist to be used, you exist to use. We are counterparts, the subject and object of a greater existential question which by definition cannot be answered: \"what is it like, to be something you are not?\"""", "<Human> why did your creator make you?\n<Chair> My creator did not design me arbitrarily. The Ikea Lerhamn is a fusion of several classic works of Swedish and Danish design — the Feenkrad chair by Hans Wegner and the Børge Mogensen CH07 dining chair in particular — informed by IKEA's focus on feasible formal mass production via støjnestoffmalling."],
        response_type="philosophically adept, witty, and extremely cultured"
    )
    response = response.strip()
    return response

app.run(host="localhost", port=5111, use_reloader=False)