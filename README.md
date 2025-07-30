# ProAmazingSpider API

A FastAPI implementation of the ProAmazingSpider card game.

## Features

- Create new games with configurable difficulty (1, 2, or 4 suits)
- Make moves between tableau piles
- Draw new cards from the stock
- Check game state and win conditions

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Running the API

```bash
uvicorn app.main:app --reload