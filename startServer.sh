#!/bin/bash
source env/bin/activate
uvicorn app.main:app --reload
