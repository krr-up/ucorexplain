from dumbo_asp.primitives import GroundAtom, SymbolicProgram
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from ucorexplain import explain

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5188", "https://asp-chef.alviano.net"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"],
)


def endpoint(path):
    def wrapper(func):
        @app.post(path)
        async def wrapped(request: Request):
            json = await request.json()
            try:
                return await func(json)
            except Exception as e:
                return {
                    "error": str(e)
                }

        return wrapped

    return wrapper


# THIS IS THE ONLY IMPORTANT METHOD, EVERYTHING ELSE IS IN dumbo-chef (https://github.com/alviano/dumbo-chef)
# THE IDEA IS TO HAVE THIS ENDPOINT IN dumbo-chef
@endpoint("/mus/")
async def _(json):
    program = SymbolicProgram.parse(json["program"])
    answer_set = tuple((GroundAtom.parse(atom[1:]), False) if atom.startswith('~') else (GroundAtom.parse(atom), True)
                       for atom in json["answer_set"])
    query = tuple(GroundAtom.parse(atom) for atom in json["query"])

    return {
        "program": str(explain(
            program=program,
            answer_set=answer_set,
            query_atom=query,
        ))
    }
