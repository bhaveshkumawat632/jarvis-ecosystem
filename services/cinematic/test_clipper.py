from tasks.autoclip_worker import process_viral_clip

# Run the task synchronously for testing
print("Testing Auto-Clipper with 'Me at the zoo' (18 seconds)...")
result = process_viral_clip("test_clip_001", "https://www.youtube.com/watch?v=jNQXAC9IVRw")
print(f"Result: {result}")
