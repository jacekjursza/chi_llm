#!/usr/bin/env python3
"""
Demonstration of chi_llm configuration hierarchy.

This example shows how configuration is loaded from different sources
and how to override settings at various levels.
"""

import os
import json
from pathlib import Path
from chi_llm import MicroLLM

def show_config_info():
    """Display current configuration information."""
    from chi_llm.models import ModelManager
    
    manager = ModelManager()
    stats = manager.get_model_stats()
    current = manager.get_current_model()
    
    print("=" * 60)
    print("CHI_LLM CONFIGURATION HIERARCHY DEMO")
    print("=" * 60)
    
    print(f"\n📊 Current Configuration:")
    print(f"   Model: {current.name} ({current.size})")
    print(f"   Model ID: {current.id}")
    print(f"   Config Source: {stats['config_source']}")
    print(f"   Config Path: {stats['config_path']}")
    print(f"   Context Window: {current.context_window:,} tokens")
    print(f"   RAM Required: {current.recommended_ram_gb}GB")
    
    print(f"\n🔍 Configuration Search Order:")
    print("   1. Environment variables (CHI_LLM_MODEL, etc.)")
    print("   2. Local .chi_llm.json (current directory)")
    print("   3. Parent .chi_llm.json (searched upward)")
    print("   4. Global config (~/.cache/chi_llm/model_config.json)")
    print("   5. Built-in defaults (gemma-270m)")
    
    return current.id

def demo_environment_override():
    """Demonstrate environment variable override."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT VARIABLE OVERRIDE")
    print("=" * 60)
    
    # Save original
    original_model = os.environ.get('CHI_LLM_MODEL')
    
    # Override with environment variable
    os.environ['CHI_LLM_MODEL'] = 'phi3-mini'
    print("\n✅ Set CHI_LLM_MODEL=phi3-mini")
    
    # Create new instance (will use env var)
    llm = MicroLLM()
    print(f"   Model loaded: {llm.model_id or 'default'}")
    
    # Restore original
    if original_model:
        os.environ['CHI_LLM_MODEL'] = original_model
    else:
        del os.environ['CHI_LLM_MODEL']

def demo_local_config():
    """Demonstrate local project configuration."""
    print("\n" + "=" * 60)
    print("LOCAL PROJECT CONFIGURATION")
    print("=" * 60)
    
    config_file = Path(".chi_llm.json")
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        print(f"\n✅ Found local config: {config_file}")
        print(f"   Default model: {config.get('default_model', 'not set')}")
        print(f"   Context: {config.get('preferred_context', 'not set')}")
        print(f"   Max tokens: {config.get('preferred_max_tokens', 'not set')}")
    else:
        print(f"\n❌ No local config found at {config_file}")
        print("   To create one:")
        print("   - Run: chi-llm models set <model-id> --local")
        print("   - Or copy examples/.chi_llm.json.example")

def demo_model_usage():
    """Demonstrate using different models."""
    print("\n" + "=" * 60)
    print("MODEL USAGE EXAMPLES")
    print("=" * 60)
    
    print("\n1. Using default configuration:")
    llm_default = MicroLLM()
    print(f"   Loaded: {llm_default.model_id or 'default model'}")
    
    print("\n2. Using specific model (if downloaded):")
    try:
        llm_specific = MicroLLM(model_id="gemma-270m")
        print(f"   Loaded: gemma-270m")
    except Exception as e:
        print(f"   Failed: {e}")
    
    print("\n3. With custom parameters:")
    llm_custom = MicroLLM(
        temperature=0.3,  # Lower = more focused
        max_tokens=512    # Shorter responses
    )
    print(f"   Temperature: 0.3 (focused)")
    print(f"   Max tokens: 512 (concise)")

def main():
    """Run configuration hierarchy demonstration."""
    
    # Show current configuration
    current_model = show_config_info()
    
    # Demonstrate different configuration methods
    demo_local_config()
    demo_environment_override()
    demo_model_usage()
    
    # Practical example
    print("\n" + "=" * 60)
    print("PRACTICAL EXAMPLE")
    print("=" * 60)
    
    print("\nGenerating text with current configuration...")
    llm = MicroLLM()
    
    # Only generate if we have the tiny model (fast)
    if current_model == "gemma-270m":
        response = llm.generate("Write a one-line Python tip:", max_tokens=50)
        print(f"Response: {response}")
    else:
        print("(Skipping generation - use gemma-270m for faster demo)")
    
    print("\n" + "=" * 60)
    print("CONFIGURATION TIPS")
    print("=" * 60)
    print("""
1. For CI/CD: Use environment variables
   export CHI_LLM_MODEL=gemma-270m
   
2. For projects: Create .chi_llm.json
   chi-llm models set qwen3-1.7b --local
   
3. For personal: Use global config
   chi-llm setup
   
4. For testing: Override in code
   llm = MicroLLM(model_id="gemma-270m")
""")

if __name__ == "__main__":
    main()