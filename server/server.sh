#!/usr/bin/env bash
source .env

uvicorn main:app --reload
