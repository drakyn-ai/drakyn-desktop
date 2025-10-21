#!/bin/bash
# Test script for CLI chat functionality

echo "Testing Drakyn CLI Chat..."
echo ""

# Test 1: Simple hello
echo "Test 1: Simple greeting"
echo "Hello, can you help me?" | python3 src/cli/cli.py chat --no-stream
echo ""

# Test 2: Gmail check (requires MCP server and credentials)
echo "Test 2: Gmail check"
echo "Can you check my Gmail and tell me about my latest email?" | python3 src/cli/cli.py chat --no-stream
echo ""

echo "Tests complete!"
