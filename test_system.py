import asyncio
import os
import sys
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_gemini_connection():
    """Test Gemini API connection"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, skipping Gemini test")
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = await asyncio.to_thread(
            model.generate_content,
            "Say 'Hello from Gemini!' and nothing else."
        )
        
        logger.info(f"Gemini response: {response.text}")
        return "Hello from Gemini" in response.text
        
    except Exception as e:
        logger.error(f"Gemini connection test failed: {e}")
        return False


async def test_groq_connection():
    """Test Groq API connection"""
    try:
        from openai import AsyncOpenAI
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not set, skipping Groq test")
            return False
            
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'Hello from Groq!' and nothing else."}],
            max_tokens=50
        )
        
        logger.info(f"Groq response: {response.choices[0].message.content}")
        return "Hello from Groq" in response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Groq connection test failed: {e}")
        return False


async def test_langgraph_import():
    """Test LangGraph imports"""
    try:
        from langgraph.graph import StateGraph
        from langgraph.checkpoint.memory import MemorySaver
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info("LangGraph imports successful")
        return True
    except Exception as e:
        logger.error(f"LangGraph import test failed: {e}")
        return False


async def test_project_config():
    """Test project configuration loading"""
    try:
        with open("project_flow.json", 'r') as f:
            config = json.load(f)
        
        logger.info(f"Project: {config.get('project_name')}")
        logger.info(f"Modules: {len(config.get('modules', []))}")
        logger.info(f"AI Routing: {len(config.get('ai_routing', {}).get('specialist_routing', {}))} specialists")
        return True
        
    except Exception as e:
        logger.error(f"Project config test failed: {e}")
        return False


async def test_ai_router_config():
    """Test AI router configuration loading"""
    try:
        with open("ai-router.json", 'r') as f:
            config = json.load(f)
        
        logger.info(f"AI Providers: {len(config.get('chain', []))}")
        for provider in config.get('chain', []):
            logger.info(f"  - {provider['name']}: {provider['model']} ({provider['role']})")
        return True
        
    except Exception as e:
        logger.error(f"AI router config test failed: {e}")
        return False


async def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        "project_flow.json",
        "ai-router.json",
        "requirements.txt",
        "main_langgraph.py",
        "langgraph_state.py",
        "langgraph_nodes.py",
        "ai_providers.py",
        ".env.example"
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        logger.error(f"Missing files: {missing}")
        return False
    
    logger.info("All required files present")
    return True


async def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("RUNNING SYSTEM TESTS")
    logger.info("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Project Config", test_project_config),
        ("AI Router Config", test_ai_router_config),
        ("LangGraph Imports", test_langgraph_import),
        ("Gemini Connection", test_gemini_connection),
        ("Groq Connection", test_groq_connection),
    ]
    
    results = {}
    for name, test_func in tests:
        logger.info(f"\nTesting: {name}")
        try:
            result = await test_func()
            results[name] = result
            logger.info(f"  Result: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            logger.error(f"  Result: ERROR - {e}")
            results[name] = False
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"  {name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)