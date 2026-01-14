"""Agent orchestrator service for managing AI agents."""
import json
import logging
import os
from pathlib import Path
from typing import Generator, Optional, Union

from app.models.agent_prompt import AgentPrompt
from app.services.nebius_client import NebiusClient
from app.services.nebius_config import NebiusConfig
from app.services.retry_handler import RetryHandler, AIErrorResponse
from app.services.video_processor import VideoProcessor, VideoFrame

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Service for orchestrating AI agent operations with Nebius AI integration."""
    
    def __init__(
        self,
        prompts_dir: Optional[str] = None,
        config: Optional[NebiusConfig] = None,
        nebius_client: Optional[NebiusClient] = None
    ):
        """
        Initialize the agent orchestrator.
        
        Args:
            prompts_dir: Path to the directory containing agent prompt JSON files.
                        Defaults to .kiro/prompts relative to project root.
            config: Nebius configuration. Uses defaults if None.
            nebius_client: Pre-configured NebiusClient. Creates new one if None.
        """
        if prompts_dir is None:
            # Default to .kiro/prompts relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            prompts_dir = str(project_root / ".kiro" / "prompts")
        
        self._prompts_dir = prompts_dir
        self._agents: dict[str, AgentPrompt] = {}
        self._loaded = False
        
        # Initialize Nebius client
        self._config = config or NebiusConfig.default()
        self._nebius_client = nebius_client or NebiusClient(config=self._config)
        self._retry_handler = RetryHandler(
            max_attempts=self._config.retry_attempts,
            base_delay=self._config.retry_delay,
            max_delay=self._config.max_retry_delay
        )
    
    def _load_agents(self) -> None:
        """Load all agent configurations from JSON files."""
        if self._loaded:
            return
        
        agent_names = ["TutorAgent", "QuizAgent", "ContentAgent"]
        
        for agent_name in agent_names:
            agent = self._load_agent(agent_name)
            if agent:
                self._agents[agent_name] = agent
        
        self._loaded = True
    
    def _load_agent(self, agent_name: str) -> Optional[AgentPrompt]:
        """
        Load a single agent configuration from its JSON file.
        
        Args:
            agent_name: Name of the agent (e.g., "TutorAgent")
            
        Returns:
            AgentPrompt if loaded successfully, None otherwise.
        """
        file_path = os.path.join(self._prompts_dir, f"{agent_name}.json")
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AgentPrompt.from_dict(data)
        except (json.JSONDecodeError, IOError):
            return None
    
    def get_agent(self, agent_name: str) -> Optional[AgentPrompt]:
        """
        Get an agent's prompt configuration.
        
        Args:
            agent_name: Name of the agent to retrieve.
            
        Returns:
            AgentPrompt if found, None otherwise.
        """
        self._load_agents()
        return self._agents.get(agent_name)
    
    def get_all_agents(self) -> dict[str, AgentPrompt]:
        """
        Get all loaded agent configurations.
        
        Returns:
            Dictionary mapping agent names to their configurations.
        """
        self._load_agents()
        return self._agents.copy()
    
    def process_chat(
        self,
        message: str,
        context: Optional[list[str]] = None,
        stream: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """
        Process a chat message through the TutorAgent with real AI.
        
        Args:
            message: The user's message/question.
            context: Optional list of content context strings.
            stream: Whether to stream the response.
            
        Returns:
            The agent's response string, or a generator for streaming.
        """
        self._load_agents()
        
        tutor = self._agents.get("TutorAgent")
        if not tutor:
            error_msg = "TutorAgent is not available."
            if stream:
                def error_stream():
                    yield error_msg
                return error_stream()
            return error_msg
        
        # Build messages array for the API call
        messages = self._build_chat_messages(tutor, message, context)
        
        try:
            # Use retry handler for resilience
            if stream:
                # For streaming, we can't use retry handler directly
                # Return the stream generator
                return self._nebius_client.chat_completion(
                    messages=messages,
                    model=self._config.tutor_model.model_id,
                    temperature=self._config.tutor_model.temperature,
                    max_tokens=self._config.tutor_model.max_tokens,
                    stream=True
                )
            else:
                # Non-streaming with retry
                response = self._retry_handler.execute(
                    self._nebius_client.chat_completion,
                    messages=messages,
                    model=self._config.tutor_model.model_id,
                    temperature=self._config.tutor_model.temperature,
                    max_tokens=self._config.tutor_model.max_tokens,
                    stream=False
                )
                return response
                
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            error_response = AIErrorResponse.from_exception(e)
            error_response.log_error(logger)
            
            error_msg = error_response.user_message
            if stream:
                def error_stream():
                    yield error_msg
                return error_stream()
            return error_msg
    
    def _build_chat_messages(
        self,
        agent: AgentPrompt,
        user_message: str,
        context: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Build the messages array for the chat API call.
        
        Args:
            agent: The agent prompt configuration.
            user_message: The user's message.
            context: Optional content context.
            
        Returns:
            List of message dictionaries with 'role' and 'content'.
        """
        messages = []
        
        # System message with agent's system prompt
        system_content = agent.system_prompt
        
        # Add context guidance if context is provided
        if context and agent.context_guidance:
            system_content += "\n\nContext Guidance:\n"
            for guidance in agent.context_guidance:
                system_content += f"- {guidance}\n"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add content context as a separate system/assistant message if provided
        if context:
            context_text = "Content Context:\n" + "\n".join(f"- {ctx}" for ctx in context)
            messages.append({
                "role": "system",
                "content": context_text
            })
        
        # User message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    @property
    def is_fallback_mode(self) -> bool:
        """Check if the orchestrator is running in fallback mode."""
        return self._nebius_client.is_fallback_mode
    
    @property
    def nebius_client(self) -> NebiusClient:
        """Get the Nebius client instance."""
        return self._nebius_client
    
    def generate_quiz(self, topic: Optional[str] = None, 
                      content: Optional[str] = None,
                      question_count: int = 5,
                      max_retries: int = 3) -> list[dict]:
        """
        Generate a quiz using the QuizAgent with real AI.
        
        Args:
            topic: Optional topic for the quiz.
            content: Optional content summary to base questions on.
            question_count: Number of questions to generate.
            max_retries: Maximum retries for invalid JSON format.
            
        Returns:
            List of quiz question dictionaries with validated structure.
        """
        self._load_agents()
        
        quiz_agent = self._agents.get("QuizAgent")
        if not quiz_agent:
            return []
        
        # Build messages for the API call
        messages = self._build_quiz_messages(quiz_agent, topic, content, question_count)
        
        # Try to generate valid quiz with retries for JSON parsing
        for attempt in range(max_retries):
            try:
                # Use retry handler for API resilience
                response = self._retry_handler.execute(
                    self._nebius_client.chat_completion,
                    messages=messages,
                    model=self._config.quiz_model.model_id,
                    temperature=self._config.quiz_model.temperature,
                    max_tokens=self._config.quiz_model.max_tokens,
                    stream=False
                )
                
                # Parse and validate the response
                questions = self._parse_quiz_response(response, question_count)
                
                if questions:
                    return questions
                
                # If parsing failed, add more explicit format instruction for retry
                if attempt < max_retries - 1:
                    logger.warning(f"Quiz generation attempt {attempt + 1} failed to produce valid JSON. Retrying with stricter prompt.")
                    messages = self._build_quiz_messages(
                        quiz_agent, topic, content, question_count, 
                        strict_format=True
                    )
                    
            except Exception as e:
                logger.error(f"Quiz generation failed on attempt {attempt + 1}: {e}")
                error_response = AIErrorResponse.from_exception(e)
                error_response.log_error(logger)
                
                if attempt >= max_retries - 1:
                    # Return fallback placeholder questions on final failure
                    return self._generate_fallback_quiz(topic, question_count)
        
        # Return fallback if all retries exhausted
        return self._generate_fallback_quiz(topic, question_count)
    
    def _build_quiz_messages(
        self,
        agent: AgentPrompt,
        topic: Optional[str],
        content: Optional[str],
        question_count: int,
        strict_format: bool = False
    ) -> list[dict]:
        """
        Build the messages array for quiz generation API call.
        
        Args:
            agent: The QuizAgent prompt configuration.
            topic: Optional topic for the quiz.
            content: Optional content to base questions on.
            question_count: Number of questions to generate.
            strict_format: Whether to use stricter JSON format instructions.
            
        Returns:
            List of message dictionaries with 'role' and 'content'.
        """
        messages = []
        
        # System message with agent's system prompt and JSON format instructions
        system_content = agent.system_prompt
        
        # Add JSON format instructions
        json_format_instruction = """

IMPORTANT: You MUST respond with ONLY a valid JSON array. Do not include any text before or after the JSON.

The response must be a JSON array of question objects with this exact structure:
[
  {
    "id": "q1",
    "question": "Your question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Explanation of why the correct answer is correct."
  }
]

Rules:
- Each question MUST have exactly 4 options
- correct_index MUST be 0, 1, 2, or 3 (the index of the correct option)
- All 4 options MUST be distinct (no duplicate options)
- Each question MUST have a non-empty explanation
- The id should be "q1", "q2", etc."""
        
        if strict_format:
            json_format_instruction += """

CRITICAL: Your previous response was not valid JSON. You MUST respond with ONLY the JSON array, starting with [ and ending with ]. No markdown code blocks, no explanations, just the raw JSON array."""
        
        system_content += json_format_instruction
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Build user message with topic/content
        user_parts = []
        
        if topic:
            user_parts.append(f"Topic: {topic}")
        
        if content:
            user_parts.append(f"Content Summary: {content}")
        
        user_parts.append(f"Generate exactly {question_count} multiple-choice questions.")
        
        if strict_format:
            user_parts.append("Remember: Respond with ONLY the JSON array, no other text.")
        
        messages.append({
            "role": "user",
            "content": "\n\n".join(user_parts)
        })
        
        return messages
    
    def _parse_quiz_response(self, response: str, expected_count: int) -> list[dict]:
        """
        Parse and validate the quiz response from the AI.
        
        Args:
            response: The raw response string from the AI.
            expected_count: Expected number of questions.
            
        Returns:
            List of validated question dictionaries, or empty list if invalid.
        """
        import re
        
        if not response:
            logger.warning("Empty response from quiz generation")
            return []
        
        # Try to extract JSON from the response
        json_str = response.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith("```"):
            # Find the JSON content between code blocks
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str)
            if match:
                json_str = match.group(1).strip()
        
        # Try to find JSON array in the response
        if not json_str.startswith('['):
            # Look for array start
            array_start = json_str.find('[')
            if array_start != -1:
                # Find matching closing bracket
                bracket_count = 0
                array_end = -1
                for i, char in enumerate(json_str[array_start:], start=array_start):
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            array_end = i + 1
                            break
                
                if array_end != -1:
                    json_str = json_str[array_start:array_end]
        
        try:
            questions_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse quiz JSON: {e}")
            return []
        
        if not isinstance(questions_data, list):
            logger.warning("Quiz response is not a list")
            return []
        
        # Validate and normalize each question
        validated_questions = []
        for i, q in enumerate(questions_data):
            validated = self._validate_quiz_question(q, i + 1)
            if validated:
                validated_questions.append(validated)
        
        # Check if we got enough valid questions
        if len(validated_questions) < expected_count:
            logger.warning(
                f"Only {len(validated_questions)} valid questions out of {expected_count} expected"
            )
        
        return validated_questions
    
    def _validate_quiz_question(self, question_data: dict, index: int) -> Optional[dict]:
        """
        Validate and normalize a single quiz question.
        
        Args:
            question_data: Raw question dictionary from AI response.
            index: Question index for ID generation.
            
        Returns:
            Validated question dict, or None if invalid.
        """
        if not isinstance(question_data, dict):
            return None
        
        # Extract and validate required fields
        question_text = question_data.get("question", "").strip()
        if not question_text:
            logger.warning(f"Question {index} has no question text")
            return None
        
        options = question_data.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            logger.warning(f"Question {index} does not have exactly 4 options")
            return None
        
        # Ensure all options are strings and non-empty
        options = [str(opt).strip() for opt in options]
        if any(not opt for opt in options):
            logger.warning(f"Question {index} has empty options")
            return None
        
        # Check for distinct options
        if len(set(options)) != 4:
            logger.warning(f"Question {index} has duplicate options")
            return None
        
        # Validate correct_index
        correct_index = question_data.get("correct_index", question_data.get("correctIndex", 0))
        try:
            correct_index = int(correct_index)
        except (ValueError, TypeError):
            correct_index = 0
        
        if not (0 <= correct_index < 4):
            logger.warning(f"Question {index} has invalid correct_index: {correct_index}")
            return None
        
        # Get explanation
        explanation = question_data.get("explanation", "").strip()
        if not explanation:
            explanation = "No explanation provided."
        
        # Get or generate ID
        question_id = question_data.get("id", f"q{index}")
        
        return {
            "id": question_id,
            "question": question_text,
            "options": options,
            "correct_index": correct_index,
            "explanation": explanation
        }
    
    def _generate_fallback_quiz(self, topic: Optional[str], question_count: int) -> list[dict]:
        """
        Generate fallback placeholder questions when AI generation fails.
        
        Args:
            topic: Optional topic for the quiz.
            question_count: Number of questions to generate.
            
        Returns:
            List of placeholder question dictionaries.
        """
        logger.warning("Using fallback quiz generation due to AI failure")
        
        placeholder_questions = []
        for i in range(question_count):
            placeholder_questions.append({
                "id": f"q{i+1}",
                "question": f"[Fallback] Sample question {i+1} about {topic or 'the content'}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": 0,
                "explanation": "[Fallback] This is a placeholder question. The AI service was unavailable."
            })
        
        return placeholder_questions
    
    def process_content(
        self,
        content_data: Union[bytes, str],
        content_type: str,
        filename: str = ""
    ) -> dict:
        """
        Process content through the ContentAgent with real AI.
        
        Args:
            content_data: Raw content data (bytes for images/binary, str for text).
            content_type: Type of content ('video', 'pdf', 'image', 'text').
            filename: Original filename for context.
            
        Returns:
            Dictionary containing extracted information with structure:
            - title: str
            - summary: str
            - key_points: list[str]
            - concepts: list[dict] with 'term' and 'definition'
            - topics: list[str]
            - source_type: str
            - processing_status: str ('complete', 'partial', 'failed')
            - error_message: str | None
        """
        self._load_agents()
        
        content_agent = self._agents.get("ContentAgent")
        if not content_agent:
            return self._create_error_content_result(
                content_type, 
                "ContentAgent is not available."
            )
        
        try:
            # Route to appropriate processing method based on content type
            content_type_lower = content_type.lower()
            
            if content_type_lower == 'image' or self._is_image_content(content_type_lower):
                return self._process_image_content(content_agent, content_data, filename)
            elif content_type_lower == 'pdf' or content_type_lower == 'text':
                return self._process_text_content(content_agent, content_data, content_type_lower, filename)
            elif content_type_lower == 'video':
                return self._process_video_content(content_agent, content_data, filename)
            else:
                # Unknown content type - try text processing
                if isinstance(content_data, str):
                    return self._process_text_content(content_agent, content_data, content_type_lower, filename)
                else:
                    return self._create_error_content_result(
                        content_type,
                        f"Unsupported content type: {content_type}"
                    )
                    
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            error_response = AIErrorResponse.from_exception(e)
            error_response.log_error(logger)
            return self._create_error_content_result(content_type, error_response.user_message)
    
    def _is_image_content(self, content_type: str) -> bool:
        """Check if content type represents an image."""
        image_types = ['image', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp']
        return any(img_type in content_type.lower() for img_type in image_types)
    
    def _process_image_content(
        self,
        agent: AgentPrompt,
        image_data: Union[bytes, str],
        filename: str
    ) -> dict:
        """
        Process image content using Vision_Model.
        
        Args:
            agent: ContentAgent prompt configuration.
            image_data: Raw image bytes or base64 string.
            filename: Original filename.
            
        Returns:
            Extracted content dictionary.
        """
        # Build the vision prompt
        prompt = self._build_vision_prompt(agent, filename)
        
        try:
            # Use retry handler for resilience
            response = self._retry_handler.execute(
                self._nebius_client.vision_completion,
                prompt=prompt,
                image_data=image_data,
                model=self._config.vision_model.model_id,
                temperature=self._config.vision_model.temperature,
                max_tokens=self._config.vision_model.max_tokens
            )
            
            # Parse the response into structured format
            return self._parse_content_response(response, 'image', filename)
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            error_response = AIErrorResponse.from_exception(e)
            return self._create_error_content_result('image', error_response.user_message)
    
    def _build_vision_prompt(self, agent: AgentPrompt, filename: str) -> str:
        """Build the prompt for vision analysis."""
        base_prompt = agent.system_prompt
        
        prompt = f"""{base_prompt}

Analyze this image and extract educational content. Provide your response in the following JSON format:
{{
    "title": "A descriptive title for the content",
    "summary": "A comprehensive summary of what the image shows",
    "key_points": ["Key point 1", "Key point 2", "Key point 3"],
    "concepts": [
        {{"term": "Concept name", "definition": "Definition of the concept"}}
    ],
    "topics": ["Topic 1", "Topic 2"]
}}

Filename: {filename}

Analyze the image thoroughly and extract all educational information visible."""
        
        return prompt
    
    def _process_video_content(
        self,
        agent: AgentPrompt,
        video_data: Union[bytes, str],
        filename: str
    ) -> dict:
        """
        Process video content by extracting key frames and analyzing with Vision_Model.
        
        Args:
            agent: ContentAgent prompt configuration.
            video_data: Raw video bytes or path to video file.
            filename: Original filename.
            
        Returns:
            Extracted content dictionary.
        """
        # Initialize video processor
        video_processor = VideoProcessor(
            max_frames=5,
            frame_quality=85,
            min_frame_interval=2.0
        )
        
        if not video_processor.is_available:
            logger.warning("Video processing unavailable - OpenCV not installed")
            return self._create_error_content_result(
                'video',
                "Video processing is not available. Please install opencv-python."
            )
        
        # Extract frames from video
        frames, error = video_processor.extract_frames(video_data, filename)
        
        if error or not frames:
            logger.error(f"Frame extraction failed: {error}")
            return self._create_error_content_result(
                'video',
                error or "Failed to extract frames from video."
            )
        
        logger.info(f"Extracted {len(frames)} frames from video: {filename}")
        
        # Analyze each frame with Vision_Model
        frame_analyses = []
        for i, frame in enumerate(frames):
            try:
                analysis = self._analyze_video_frame(agent, frame, filename, i + 1, len(frames))
                if analysis:
                    frame_analyses.append(analysis)
            except Exception as e:
                logger.warning(f"Failed to analyze frame {i + 1}: {e}")
                # Continue with other frames
        
        if not frame_analyses:
            return self._create_error_content_result(
                'video',
                "Failed to analyze any frames from the video."
            )
        
        # Combine frame analyses into final result
        return self._combine_video_frame_analyses(frame_analyses, filename)
    
    def _analyze_video_frame(
        self,
        agent: AgentPrompt,
        frame: VideoFrame,
        filename: str,
        frame_index: int,
        total_frames: int
    ) -> Optional[dict]:
        """
        Analyze a single video frame using Vision_Model.
        
        Args:
            agent: ContentAgent prompt configuration.
            frame: VideoFrame to analyze.
            filename: Original video filename.
            frame_index: Current frame index (1-based).
            total_frames: Total number of frames being analyzed.
            
        Returns:
            Analysis result dictionary or None if failed.
        """
        prompt = self._build_video_frame_prompt(
            agent, filename, frame.timestamp_seconds, frame_index, total_frames
        )
        
        try:
            response = self._retry_handler.execute(
                self._nebius_client.vision_completion,
                prompt=prompt,
                image_data=frame.image_data,
                model=self._config.vision_model.model_id,
                temperature=self._config.vision_model.temperature,
                max_tokens=self._config.vision_model.max_tokens
            )
            
            return self._parse_content_response(response, 'video_frame', filename)
            
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return None
    
    def _build_video_frame_prompt(
        self,
        agent: AgentPrompt,
        filename: str,
        timestamp: float,
        frame_index: int,
        total_frames: int
    ) -> str:
        """Build the prompt for video frame analysis."""
        base_prompt = agent.system_prompt
        
        prompt = f"""{base_prompt}

You are analyzing frame {frame_index} of {total_frames} from a video file.
This frame is from approximately {timestamp:.1f} seconds into the video.

Analyze this video frame and extract educational content. Provide your response in the following JSON format:
{{
    "title": "A descriptive title for what this frame shows",
    "summary": "A description of what is shown in this frame",
    "key_points": ["Key observation 1", "Key observation 2"],
    "concepts": [
        {{"term": "Concept name", "definition": "Definition if visible"}}
    ],
    "topics": ["Topic 1", "Topic 2"]
}}

Video filename: {filename}
Frame timestamp: {timestamp:.1f}s

Analyze the frame thoroughly and extract all educational information visible."""
        
        return prompt
    
    def _combine_video_frame_analyses(
        self,
        frame_analyses: list[dict],
        filename: str
    ) -> dict:
        """
        Combine analyses from multiple video frames into a single result.
        
        Args:
            frame_analyses: List of analysis results from each frame.
            filename: Original video filename.
            
        Returns:
            Combined extraction result.
        """
        # Generate title from filename or first frame
        title = filename.rsplit('.', 1)[0] if '.' in filename else filename
        if frame_analyses and frame_analyses[0].get('title'):
            first_title = frame_analyses[0].get('title', '')
            if first_title and not first_title.startswith('['):
                title = first_title
        
        # Combine summaries from all frames
        summaries = []
        for i, analysis in enumerate(frame_analyses):
            summary = analysis.get('summary', '')
            if summary and not summary.startswith('['):
                summaries.append(f"[Frame {i+1}] {summary}")
        
        combined_summary = ' '.join(summaries) if summaries else f"Video analysis of {filename}"
        
        # Combine and deduplicate key points
        all_key_points = []
        seen_points = set()
        for analysis in frame_analyses:
            for point in analysis.get('key_points', []):
                if point and not point.startswith('['):
                    point_lower = point.lower().strip()
                    if point_lower not in seen_points:
                        seen_points.add(point_lower)
                        all_key_points.append(point)
        
        # Combine and deduplicate concepts
        all_concepts = []
        seen_terms = set()
        for analysis in frame_analyses:
            for concept in analysis.get('concepts', []):
                term = concept.get('term', '').lower().strip()
                if term and term not in seen_terms:
                    seen_terms.add(term)
                    all_concepts.append(concept)
        
        # Combine and deduplicate topics
        all_topics = []
        seen_topics = set()
        for analysis in frame_analyses:
            for topic in analysis.get('topics', []):
                if topic:
                    topic_lower = topic.lower().strip()
                    if topic_lower not in seen_topics:
                        seen_topics.add(topic_lower)
                        all_topics.append(topic)
        
        return {
            "title": title,
            "summary": combined_summary,
            "key_points": all_key_points[:10],  # Limit to top 10
            "concepts": all_concepts[:10],  # Limit to top 10
            "topics": all_topics[:10],  # Limit to top 10
            "source_type": "video",
            "processing_status": "complete",
            "error_message": None
        }
    
    def _process_text_content(
        self,
        agent: AgentPrompt,
        content_data: Union[bytes, str],
        content_type: str,
        filename: str
    ) -> dict:
        """
        Process text/PDF content using Text_Model with chunking for large documents.
        
        Args:
            agent: ContentAgent prompt configuration.
            content_data: Text content (string or bytes).
            content_type: Type of content ('pdf', 'text').
            filename: Original filename.
            
        Returns:
            Extracted content dictionary.
        """
        # Convert bytes to string if needed
        if isinstance(content_data, bytes):
            try:
                text_content = content_data.decode('utf-8')
            except UnicodeDecodeError:
                text_content = content_data.decode('latin-1', errors='replace')
        else:
            text_content = content_data
        
        # Check if document needs chunking
        # Approximate token limit - use ~3000 tokens worth of text per chunk
        # Assuming ~4 chars per token on average
        max_chunk_chars = 12000
        
        if len(text_content) > max_chunk_chars:
            return self._process_large_document(agent, text_content, content_type, filename, max_chunk_chars)
        else:
            return self._process_single_chunk(agent, text_content, content_type, filename)
    
    def _process_single_chunk(
        self,
        agent: AgentPrompt,
        text_content: str,
        content_type: str,
        filename: str
    ) -> dict:
        """Process a single chunk of text content."""
        messages = self._build_content_messages(agent, text_content, content_type, filename)
        
        try:
            response = self._retry_handler.execute(
                self._nebius_client.chat_completion,
                messages=messages,
                model=self._config.content_model.model_id,
                temperature=self._config.content_model.temperature,
                max_tokens=self._config.content_model.max_tokens,
                stream=False
            )
            
            return self._parse_content_response(response, content_type, filename)
            
        except Exception as e:
            logger.error(f"Text content processing failed: {e}")
            error_response = AIErrorResponse.from_exception(e)
            return self._create_error_content_result(content_type, error_response.user_message)
    
    def _process_large_document(
        self,
        agent: AgentPrompt,
        text_content: str,
        content_type: str,
        filename: str,
        max_chunk_chars: int
    ) -> dict:
        """
        Process a large document by chunking and combining results.
        
        Args:
            agent: ContentAgent prompt configuration.
            text_content: Full text content.
            content_type: Type of content.
            filename: Original filename.
            max_chunk_chars: Maximum characters per chunk.
            
        Returns:
            Combined extracted content dictionary.
        """
        # Split into chunks
        chunks = self._chunk_document(text_content, max_chunk_chars)
        logger.info(f"Processing large document in {len(chunks)} chunks")
        
        # Process each chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i + 1}/{len(chunks)}")
            try:
                chunk_result = self._process_single_chunk(
                    agent, chunk, content_type, f"{filename} (part {i + 1}/{len(chunks)})"
                )
                if chunk_result.get('processing_status') != 'failed':
                    chunk_results.append(chunk_result)
            except Exception as e:
                logger.warning(f"Failed to process chunk {i + 1}: {e}")
                # Continue with other chunks
        
        if not chunk_results:
            return self._create_error_content_result(
                content_type,
                "Failed to process any chunks of the document."
            )
        
        # Combine results from all chunks
        return self._combine_chunk_results(chunk_results, content_type, filename)
    
    def _chunk_document(self, text: str, max_chunk_chars: int) -> list[str]:
        """
        Split document into chunks, trying to break at paragraph boundaries.
        
        Args:
            text: Full document text.
            max_chunk_chars: Maximum characters per chunk.
            
        Returns:
            List of text chunks.
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        for para in paragraphs:
            # If adding this paragraph would exceed limit
            if len(current_chunk) + len(para) + 2 > max_chunk_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If single paragraph is too long, split it
                if len(para) > max_chunk_chars:
                    # Split by sentences or fixed size
                    para_chunks = self._split_long_paragraph(para, max_chunk_chars)
                    chunks.extend(para_chunks[:-1])
                    current_chunk = para_chunks[-1] if para_chunks else ""
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_chunk_chars]]
    
    def _split_long_paragraph(self, text: str, max_chars: int) -> list[str]:
        """Split a long paragraph into smaller chunks."""
        chunks = []
        
        # Try to split by sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If single sentence is too long, split by fixed size
                if len(sentence) > max_chars:
                    for i in range(0, len(sentence), max_chars):
                        chunks.append(sentence[i:i + max_chars])
                    current_chunk = ""
                else:
                    current_chunk = sentence
            else:
                current_chunk = (current_chunk + " " + sentence).strip()
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _combine_chunk_results(
        self,
        chunk_results: list[dict],
        content_type: str,
        filename: str
    ) -> dict:
        """
        Combine results from multiple chunks into a single result.
        
        Args:
            chunk_results: List of extraction results from each chunk.
            content_type: Type of content.
            filename: Original filename.
            
        Returns:
            Combined extraction result.
        """
        # Use first chunk's title or generate one
        title = chunk_results[0].get('title', 'Extracted Content')
        if '(part' in title:
            # Remove part indicator from title
            title = title.split('(part')[0].strip()
        
        # Combine summaries
        summaries = [r.get('summary', '') for r in chunk_results if r.get('summary')]
        combined_summary = ' '.join(summaries)
        
        # Combine and deduplicate key points
        all_key_points = []
        seen_points = set()
        for result in chunk_results:
            for point in result.get('key_points', []):
                point_lower = point.lower().strip()
                if point_lower not in seen_points:
                    seen_points.add(point_lower)
                    all_key_points.append(point)
        
        # Combine and deduplicate concepts
        all_concepts = []
        seen_terms = set()
        for result in chunk_results:
            for concept in result.get('concepts', []):
                term = concept.get('term', '').lower().strip()
                if term and term not in seen_terms:
                    seen_terms.add(term)
                    all_concepts.append(concept)
        
        # Combine and deduplicate topics
        all_topics = []
        seen_topics = set()
        for result in chunk_results:
            for topic in result.get('topics', []):
                topic_lower = topic.lower().strip()
                if topic_lower not in seen_topics:
                    seen_topics.add(topic_lower)
                    all_topics.append(topic)
        
        return {
            "title": title,
            "summary": combined_summary,
            "key_points": all_key_points[:10],  # Limit to top 10
            "concepts": all_concepts[:10],  # Limit to top 10
            "topics": all_topics[:10],  # Limit to top 10
            "source_type": content_type,
            "processing_status": "complete",
            "error_message": None
        }
    
    def _build_content_messages(
        self,
        agent: AgentPrompt,
        text_content: str,
        content_type: str,
        filename: str
    ) -> list[dict]:
        """Build messages for text content processing."""
        messages = []
        
        # System message with agent prompt and JSON format instructions
        system_content = agent.system_prompt + """

IMPORTANT: You MUST respond with ONLY valid JSON. Do not include any text before or after the JSON.

Respond in this exact JSON format:
{
    "title": "A descriptive title for the content",
    "summary": "A comprehensive summary of the content",
    "key_points": ["Key point 1", "Key point 2", "Key point 3"],
    "concepts": [
        {"term": "Concept name", "definition": "Definition of the concept"}
    ],
    "topics": ["Topic 1", "Topic 2"]
}

Rules:
- title: A clear, descriptive title
- summary: A comprehensive summary (2-4 sentences)
- key_points: At least 3 key points, each as a complete sentence
- concepts: Important terms with their definitions
- topics: Main topics covered in the content"""
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # User message with the content
        user_content = f"""Content Type: {content_type}
Filename: {filename}

Content to analyze:
{text_content}

Extract the key information from this content and respond with ONLY the JSON object."""
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def _parse_content_response(
        self,
        response: str,
        content_type: str,
        filename: str
    ) -> dict:
        """
        Parse the AI response into structured content extraction result.
        
        Args:
            response: Raw response from AI.
            content_type: Type of content processed.
            filename: Original filename.
            
        Returns:
            Structured extraction result dictionary.
        """
        import re
        
        if not response:
            return self._create_fallback_content_result(content_type, filename)
        
        # Try to extract JSON from response
        json_str = response.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith("```"):
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str)
            if match:
                json_str = match.group(1).strip()
        
        # Try to find JSON object in response
        if not json_str.startswith('{'):
            obj_start = json_str.find('{')
            if obj_start != -1:
                # Find matching closing brace
                brace_count = 0
                obj_end = -1
                for i, char in enumerate(json_str[obj_start:], start=obj_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            obj_end = i + 1
                            break
                
                if obj_end != -1:
                    json_str = json_str[obj_start:obj_end]
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse content JSON: {e}")
            # Try to extract information from plain text response
            return self._extract_from_plain_text(response, content_type, filename)
        
        # Validate and normalize the response
        return self._normalize_content_result(data, content_type, filename)
    
    def _normalize_content_result(
        self,
        data: dict,
        content_type: str,
        filename: str
    ) -> dict:
        """Normalize and validate content extraction result."""
        title = data.get('title', '').strip()
        if not title:
            title = filename or 'Extracted Content'
        
        summary = data.get('summary', '').strip()
        if not summary:
            summary = 'No summary available.'
        
        key_points = data.get('key_points', [])
        if not isinstance(key_points, list):
            key_points = []
        key_points = [str(p).strip() for p in key_points if p]
        if not key_points:
            key_points = ['No key points extracted.']
        
        concepts = data.get('concepts', [])
        if not isinstance(concepts, list):
            concepts = []
        normalized_concepts = []
        for c in concepts:
            if isinstance(c, dict) and c.get('term'):
                normalized_concepts.append({
                    'term': str(c.get('term', '')).strip(),
                    'definition': str(c.get('definition', '')).strip()
                })
        
        topics = data.get('topics', [])
        if not isinstance(topics, list):
            topics = []
        topics = [str(t).strip() for t in topics if t]
        
        return {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "concepts": normalized_concepts,
            "topics": topics,
            "source_type": content_type,
            "processing_status": "complete",
            "error_message": None
        }
    
    def _extract_from_plain_text(
        self,
        response: str,
        content_type: str,
        filename: str
    ) -> dict:
        """
        Extract information from plain text response when JSON parsing fails.
        
        Args:
            response: Plain text response from AI.
            content_type: Type of content.
            filename: Original filename.
            
        Returns:
            Best-effort extraction result.
        """
        # Use the response as summary
        lines = response.strip().split('\n')
        
        # Try to extract title from first line
        title = lines[0].strip() if lines else filename
        if len(title) > 100:
            title = filename or 'Extracted Content'
        
        # Use rest as summary
        summary = ' '.join(lines[1:]).strip() if len(lines) > 1 else response[:500]
        
        return {
            "title": title,
            "summary": summary,
            "key_points": ["Content was processed but structured extraction failed."],
            "concepts": [],
            "topics": [],
            "source_type": content_type,
            "processing_status": "partial",
            "error_message": "Could not parse structured response from AI."
        }
    
    def _create_fallback_content_result(
        self,
        content_type: str,
        filename: str
    ) -> dict:
        """Create a fallback result when AI is unavailable."""
        return {
            "title": filename or "Uploaded Content",
            "summary": f"[Fallback Mode] Content of type '{content_type}' was uploaded. "
                      "AI analysis is currently unavailable.",
            "key_points": [
                "[Fallback] Content uploaded successfully",
                "[Fallback] AI analysis unavailable - please configure NEBIUS_API_KEY"
            ],
            "concepts": [],
            "topics": [],
            "source_type": content_type,
            "processing_status": "partial",
            "error_message": "AI service unavailable. Using fallback mode."
        }
    
    def _create_error_content_result(
        self,
        content_type: str,
        error_message: str
    ) -> dict:
        """Create an error result for failed processing."""
        return {
            "title": "Processing Failed",
            "summary": f"Failed to process {content_type} content.",
            "key_points": [],
            "concepts": [],
            "topics": [],
            "source_type": content_type,
            "processing_status": "failed",
            "error_message": error_message
        }
    
    def reload_agents(self) -> None:
        """Force reload of all agent configurations."""
        self._agents.clear()
        self._loaded = False
        self._load_agents()


# Global agent orchestrator instance
agent_orchestrator = AgentOrchestrator()
