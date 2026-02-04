import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.requirement_agent import RequirementAgent

def main():
    """Main function to run the requirement agent"""
    
    # Path to email conversations file
    email_file = os.path.join(
        os.path.dirname(__file__),
        '../email_conversations.txt'
    )
    
    # Check if file exists
    if not os.path.exists(email_file):
        print(f"❌ Error: Email file not found at {email_file}")
        return
    
    # Initialize the requirement agent (with AI enabled)
    agent = RequirementAgent(use_ai=True)
    
    try:
        # Process all conversations and store only requirements
        agent.process_all_requirements(email_file)
        
        # Display summary
        agent.get_requirements_summary()
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close MongoDB connection
        agent.close()
        print("\n🔒 Connection closed")

if __name__ == "__main__":
    main()
