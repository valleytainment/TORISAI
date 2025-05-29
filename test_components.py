import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from agent import Agent
from memory_manager import Memory
from tools import Tools
from gui_automation import GUIAutomation

def test_memory_manager():
    """Test the memory manager module"""
    print("\n=== Testing Memory Manager ===")
    memory = Memory()
    
    # Test adding an interaction
    result = memory.add_interaction("Test question", "Test answer", "planner")
    print(f"Add interaction result: {result}")
    
    # Test retrieving history
    history = memory.get_recent_history(1)
    print(f"Recent history: {history}")
    
    # Test searching memory
    search_results = memory.search_memory("test")
    print(f"Search results count: {len(search_results)}")
    
    return True

def test_tools():
    """Test the tools module"""
    print("\n=== Testing Tools ===")
    tools = Tools()
    
    # Test web search
    search_result = tools.web_search("Python programming")
    print(f"Web search returned {len(search_result)} characters")
    
    # Test file operations
    file_path = os.path.join(tools.memory_dir, "test_file.txt")
    write_result = tools.file_operations("write", file_path, "Test content")
    print(f"File write result: {write_result}")
    
    read_result = tools.file_operations("read", file_path)
    print(f"File read result: {read_result}")
    
    list_result = tools.file_operations("list", tools.memory_dir)
    print(f"Directory list result: {list_result}")
    
    return True

def test_agent():
    """Test the agent module"""
    print("\n=== Testing Agent ===")
    agent = Agent(agent_type="planner", model="llama3:8b")
    
    # Test system prompt
    system_prompt = agent.get_system_prompt()
    print(f"System prompt length: {len(system_prompt)} characters")
    
    # Test changing agent type
    change_result = agent.change_agent_type("coder")
    print(f"Change agent type result: {change_result}")
    
    # Test changing model
    model_result = agent.change_model("qwen:7b")
    print(f"Change model result: {model_result}")
    
    return True

def test_gui_automation():
    """Test the GUI automation module"""
    print("\n=== Testing GUI Automation ===")
    gui = GUIAutomation()
    
    # Test screen size
    screen_size = gui.get_screen_size()
    print(f"Screen size: {screen_size}")
    
    # Test screenshot
    screenshot_path = gui.capture_screen()
    print(f"Screenshot saved to: {screenshot_path}")
    
    return True

def main():
    """Run all tests"""
    print("Starting TORIS AI component tests...")
    
    tests = [
        test_memory_manager,
        test_tools,
        test_agent,
        test_gui_automation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"Error in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))
    
    # Print summary
    print("\n=== Test Summary ===")
    all_passed = True
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
