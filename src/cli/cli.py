#!/usr/bin/env python3
"""
Drakyn CLI - Command-line interface for the Drakyn AI Agent
"""

import click
import requests
import sys
from typing import Optional
import json

API_BASE_URL = "http://127.0.0.1:8000"


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Drakyn AI Agent - CLI Interface

    A command-line interface for interacting with your local AI agent.
    """
    pass


@cli.command()
def status():
    """Check server and model status"""
    try:
        click.echo(click.style("Checking server status...\n", fg="cyan"))

        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        data = response.json()

        click.echo(click.style("✓ Server is running", fg="green"))
        click.echo(f"  Engine: {click.style(data.get('inference_engine', 'vllm'), fg='yellow')}")

        if data.get('current_model'):
            click.echo(f"  Current Model: {click.style(data['current_model'], fg='yellow')}")
        else:
            click.echo(click.style("  No model loaded", dim=True))

        if data.get('openai_compatible_url'):
            click.echo(f"  External Server: {click.style(data['openai_compatible_url'], fg='yellow')}")

    except requests.exceptions.ConnectionError:
        click.echo(click.style("✗ Server is not running", fg="red"))
        click.echo(click.style(f"  Expected at: {API_BASE_URL}", dim=True))
        click.echo(click.style("  Start it with: npm run server (Linux/Mac) or npm run server:win (Windows)", dim=True))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
def models():
    """List available and loaded models"""
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=5)
        data = response.json()

        models_list = data.get('models', [])

        if not models_list:
            click.echo(click.style("No models currently loaded", dim=True))
        else:
            click.echo(click.style("Loaded Models:", fg="cyan", bold=True))
            for model in models_list:
                name = model.get('name', 'Unknown')
                active = model.get('active', False)
                if active:
                    click.echo(f"  • {click.style(name, fg='green')} {click.style('(active)', fg='green', dim=True)}")
                else:
                    click.echo(f"  • {name}")

    except requests.exceptions.ConnectionError:
        click.echo(click.style("✗ Server is not running", fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument('model_name')
@click.option('--gpu-memory', default=0.9, help='GPU memory utilization (0.1-1.0)')
@click.option('--tensor-parallel', default=1, help='Tensor parallel size')
def load(model_name: str, gpu_memory: float, tensor_parallel: int):
    """Load a model

    MODEL_NAME: Name or path of the model to load

    Examples:
      drakyn load qwen2.5-coder:3b
      drakyn load claude-sonnet-4-5
    """
    try:
        click.echo(f"Loading model: {click.style(model_name, fg='yellow')}...")

        payload = {
            "model_name_or_path": model_name,
            "gpu_memory_utilization": gpu_memory,
            "tensor_parallel_size": tensor_parallel
        }

        response = requests.post(f"{API_BASE_URL}/load_model", json=payload, timeout=30)
        data = response.json()

        if response.status_code == 200:
            click.echo(click.style(f"✓ {data.get('message', 'Model loaded')}", fg="green"))
        else:
            click.echo(click.style(f"✗ {data.get('detail', 'Failed to load model')}", fg="red"))
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        click.echo(click.style("✗ Server is not running", fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option('--stream/--no-stream', default=True, help='Stream the response')
def chat(stream: bool):
    """Start an interactive chat session with the agent

    Type your messages and press Enter. Type 'exit' or 'quit' to end the session.
    """
    try:
        # Check if server is running
        requests.get(f"{API_BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        click.echo(click.style("✗ Server is not running", fg="red"))
        click.echo(click.style("  Start it with: npm run server", dim=True))
        sys.exit(1)

    click.echo(click.style("Drakyn Agent Chat", fg="cyan", bold=True))
    click.echo(click.style("Type your message and press Enter. Type 'exit' or 'quit' to end.\n", dim=True))

    while True:
        try:
            # Get user input
            user_input = click.prompt(click.style("You", fg="blue"), type=str)

            if user_input.lower() in ['exit', 'quit', 'q']:
                click.echo(click.style("\nGoodbye!", fg="cyan"))
                break

            # Send to agent
            click.echo(click.style("Agent", fg="green") + ": ", nl=False)

            if stream:
                # Stream response
                response = requests.post(
                    f"{API_BASE_URL}/v1/agent/chat",
                    json={"message": user_input, "stream": True},
                    stream=True,
                    timeout=120
                )

                answer = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])

                                if data.get('type') == 'thinking':
                                    click.echo(click.style(f"\n[Thinking...] ", fg="yellow", dim=True), nl=False)
                                elif data.get('type') == 'tool_call':
                                    tool_name = data.get('tool_name', 'unknown')
                                    click.echo(click.style(f"\n[Using tool: {tool_name}] ", fg="cyan", dim=True), nl=False)
                                elif data.get('type') == 'answer':
                                    answer = data.get('content', '')
                                    click.echo(answer)
                                elif data.get('type') == 'error':
                                    click.echo(click.style(f"Error: {data.get('error')}", fg="red"))

                            except json.JSONDecodeError:
                                pass

                click.echo()  # New line after response

            else:
                # Non-streaming response
                response = requests.post(
                    f"{API_BASE_URL}/v1/agent/chat",
                    json={"message": user_input, "stream": False},
                    timeout=120
                )
                data = response.json()

                if 'answer' in data:
                    click.echo(data['answer'])
                elif 'error' in data:
                    click.echo(click.style(f"Error: {data['error']}", fg="red"))
                else:
                    click.echo(click.style("No response from agent", fg="red"))

                click.echo()

        except KeyboardInterrupt:
            click.echo(click.style("\n\nGoodbye!", fg="cyan"))
            break
        except Exception as e:
            click.echo(click.style(f"\nError: {e}", fg="red"))


if __name__ == '__main__':
    cli()
