# ProAmazingSpider API

A FastAPI implementation of the ProAmazingSpider card game.

## Features

- Create new games with difficulty 0–9, 1/2/4 suits, and optional seeded deals
- Daily challenge: `GET /api/v1/daily` returns a shared date/seed for every player
- Hints: `POST /api/v1/hint` suggests a move without changing the board
- Make moves between tableau piles
- Draw new cards from the stock
- Check game state and win conditions
- **Comprehensive card arrangement logging** for debugging and analysis

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
```

## Logging Configuration

The API includes comprehensive card arrangement logging that tracks:

- **Game State Logging**: Complete card arrangements for each pile
- **Operation Tracking**: Start/end of each API operation with request IDs
- **Move Analysis**: Detailed move operations with before/after state comparisons
- **State Changes**: Tracking of card movements, completed sequences, and stock changes

### Configuration Options

Logging can be configured via environment variables or settings:

- `ENABLE_CARD_LOGGING`: Enable/disable card arrangement logging (default: True)
- `LOG_LEVEL`: Set logging level (default: INFO)
- `LOG_FILE`: Specify log file path (default: card_arrangements.log)

### Log Output

Logs are written to both console and file (`card_arrangements.log`) in JSON format for easy parsing and analysis.

Example log entry:
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "operation": "move",
  "game_state": {
    "piles": [
      {
        "pile_index": 0,
        "card_count": 5,
        "last_movable_index": 2,
        "cards": [
          {
            "position": 0,
            "rank": 13,
            "suit": 1,
            "is_face_up": true,
            "movable": true
          }
        ]
      }
    ]
  }
}
```