from fastapi import FastAPI, Form, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from google.cloud import firestore
from google.auth.transport import requests
from google.oauth2 import id_token
from urllib.parse import quote
from typing import List, Optional
from fastapi import Form

app = FastAPI()
db = firestore.Client()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

firebase_request_adapter = requests.Request()

async def verify_firebase_token(token: str):
    if not token:
        return None
    try:
        user_token = id_token.verify_firebase_token(token, firebase_request_adapter)
        return user_token
    except ValueError as err:
        print(f"Token verification failed: {err}")
        return None
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token_str = request.cookies.get("token")
    user_info = None
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)
    
    attribute = request.query_params.get("attribute_name")
    min_value = request.query_params.get("min_value_case_2_name")
    max_value = request.query_params.get("max_value_case_2_name")
    string_value = request.query_params.get("string_value_case_1_name")

    query = db.collection('evs')

    if attribute in ['year', 'battery_size', 'wltp_range', 'cost', 'power'] and min_value and max_value:
        query = query.where(attribute, '>=', float(min_value)).where(attribute, '<=', float(max_value))
    elif attribute and string_value:
        query = query.where(attribute, '==', string_value)

    evs = query.stream()

    evs_data = []
    for ev in query.stream():
        ev_dict = ev.to_dict()
        ev_dict["id"] = ev.id
        evs_data.append(ev_dict)
    
    return templates.TemplateResponse("main.html", {"request": request, "user_info": user_info, "evs": evs_data})
@app.get("/add-ev", response_class=HTMLResponse)
async def add_ev_page(request: Request):
    id_token_str = request.cookies.get("token")
    user_info = None
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)
    if not user_info:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse("add_ev.html", {"request": request})
@app.post("/create-ev")
async def create_ev(request: Request, name: str = Form(...), manufacturer: str = Form(...), year: int = Form(...), battery_size: float = Form(...), wltp_range: int = Form(...), cost: float = Form(...), power: int = Form(...)):    
    
    evs_ref = db.collection('evs')
    query = evs_ref.where('name', '==', name)
    results = query.stream()
    count = 0

    for result in results:
        count += 1
    
    if count > 0:
        raise HTTPException(status_code=400, detail="An EV with this name already exists")

    ev_data = {
        'name': name,
        'manufacturer': manufacturer,
        'year': year,
        'battery_size': battery_size,
        'wltp_range': wltp_range,
        'cost': cost,
        'power': power,
        'average_rating': 0.0,
    }
    ignore_first_arg, doc_ref = db.collection('evs').add(ev_data)

    website_url = f"/ev/{doc_ref.id}"
    doc_ref.update({'website': website_url})

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
@app.get("/remove-ev", response_class=HTMLResponse)
async def delete_ev_page(request: Request):
    id_token_str = request.cookies.get("token")
    user_info = None
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)
    if not user_info:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    evs_ref = db.collection('evs')
    evs = evs_ref.stream()
    evs_data = []
    for ev in evs:
        ev_dict = ev.to_dict()
        ev_dict["id"] = ev.id
        evs_data.append(ev_dict)
    return templates.TemplateResponse("delete_ev.html", {"request": request, "evs_data": evs_data})
@app.post("/delete-ev")
async def delete_ev_post(request: Request, ev_name: str = Form(...)):
    id_token_str = request.cookies.get("token")
    user_info = None
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)
    if not user_info:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    evs_ref = db.collection('evs')
    query = evs_ref.where('name', '==', ev_name).limit(1)
    results = list(query.stream())
    
    if len(results) == 1:
        results[0].reference.delete()
    else:
        raise HTTPException(status_code=400, detail="No EV with this name exists")
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
@app.get("/modify-ev", response_class=HTMLResponse)
async def modify_ev_page(request: Request, ev_id: str):
    id_token_str = request.cookies.get("token")
    user_info = None
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)
    if not user_info:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    evs_ref = db.collection('evs')
    ev_document = evs_ref.document(ev_id).get()
    if not ev_document.exists:
        raise HTTPException(status_code=404, detail="EV not found")

    ev_data = ev_document.to_dict()
    ev_data['id'] = ev_id

    return templates.TemplateResponse("edit_ev.html", {"request": request, "ev": ev_data})
@app.post("/edit-ev")
async def edit_ev(request: Request, ev_id: str = Form(...), ev_name: str = Form(...), manufacturer: str = Form(...), year: int = Form(...), battery_size: float = Form(...), wltp_range: int = Form(...), cost: float = Form(...), power: int = Form(...)):
    id_token_str = request.cookies.get("token")
    user_info = None
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)
    if not user_info:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    update_data = {
        'name': ev_name,
        'manufacturer': manufacturer,
        'year': year,
        'battery_size': battery_size,
        'wltp_range': wltp_range,
        'cost': cost,
        'power': power,
    }

    evs_ref = db.collection('evs')
    evs_ref.document(ev_id).update(update_data)

    return RedirectResponse(url=f"/ev/{ev_id}", status_code=status.HTTP_303_SEE_OTHER)
@app.get("/ev/{ev_id}", response_class=HTMLResponse)
async def ev_details(request: Request, ev_id: str):
    ev_doc = db.collection('evs').document(ev_id).get()
    if not ev_doc.exists:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    ev_data = ev_doc.to_dict()
    ev_data['id'] = ev_id

    comments_query = db.collection('comments').where('ev_id', '==', ev_id).stream()
    comments = [comment.to_dict() for comment in comments_query]

    comments.sort(key=lambda x: x['date_posted'], reverse=True)

    user_info = None
    id_token_str = request.cookies.get("token")
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)

    return templates.TemplateResponse("ev_details.html", {"request": request, "ev": ev_data, "comments": comments, "user_info": user_info})
@app.post("/ev/{ev_id}/add-comment")
async def add_comment(ev_id: str, request: Request, comment: str = Form(...), rating: int = Form(...)):
    id_token_str = request.cookies.get("token")
    user_info = None
    if id_token_str:
        user_info = await verify_firebase_token(id_token_str)
    if not user_info:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    comment_data = {
        'ev_id': ev_id,
        'comment': comment,
        'rating': rating,
        'date_posted': firestore.SERVER_TIMESTAMP
    }
    db.collection('comments').add(comment_data)
    comments_query = db.collection('comments').where('ev_id', '==', ev_id).stream()
    
    total_rating = 0
    count = 0
    for comment in comments_query:
        total_rating += comment.to_dict().get('rating', 0)
        count += 1
    if count > 0:
        new_average_rating = total_rating / count
    else:
        new_average_rating = 0
    
    db.collection('evs').document(ev_id).update({'average_rating': new_average_rating})

    return RedirectResponse(url=f"/ev/{ev_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/compare", response_class=HTMLResponse)
async def compare_evs(request: Request, ev_id_1: str = Form(...), ev_id_2: str = Form(...)):

    ev_doc_1 = db.collection('evs').document(ev_id_1).get().to_dict()
    ev_doc_2 = db.collection('evs').document(ev_id_2).get().to_dict()
    
    if not ev_doc_1 or not ev_doc_2:
        print("Atlease one of the EVs does not exist")
    
    comparisons = [
        ev_doc_1['year'] > ev_doc_2['year'],
        ev_doc_1['battery_size'] > ev_doc_2['battery_size'],
        ev_doc_1['wltp_range'] > ev_doc_2['wltp_range'],
        ev_doc_1['cost'] < ev_doc_2['cost'],
        ev_doc_1['power'] > ev_doc_2['power'],
        ev_doc_1.get('average_rating', 0) > ev_doc_2.get('average_rating', 0),
    ]

    evs = [ev_doc_1, ev_doc_2]

    return templates.TemplateResponse("compare.html", {
        "request": request,
        "comparisons": comparisons,
        "evs": evs,
    })