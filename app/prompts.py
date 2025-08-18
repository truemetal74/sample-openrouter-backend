from typing import Dict, Any
from app.models import PromptName
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages server-stored prompt templates with variable substitution."""
    
    # Server-stored prompt templates
    PROMPTS = {
        PromptName.COMPANY_ANALYSIS: """
Analyze the following company and provide insights:

Company: {company_name}
Industry: {industry}
Additional Context: {additional_context if additional_context else 'None provided'}

Please provide:
1. Market position analysis
2. Key strengths and weaknesses
3. Competitive landscape overview
4. Growth opportunities
5. Risk factors
""",
        
        PromptName.TEXT_SUMMARY: """
Please provide a comprehensive summary of the following text:

Text: {text}

Requirements:
- Maintain key information and context
- Highlight main points and conclusions
- Keep the summary concise but informative
- Preserve the original tone and style where appropriate
""",
        
        PromptName.CODE_REVIEW: """
Please review the following code and provide feedback:

Code:
{code}

Language: {language if language else 'Not specified'}

Please provide:
1. Code quality assessment
2. Potential bugs or issues
3. Security concerns
4. Performance improvements
5. Best practices recommendations
6. Overall rating (1-10)
""",
        
        PromptName.GENERAL_QUESTION: """
Please answer the following question:

Question: {question}

Additional Context: {context if context else 'None provided'}

Please provide a comprehensive and accurate answer based on the information provided.
"""
    }
    
    @classmethod
    def get_prompt(cls, prompt_name: PromptName, data: Dict[str, Any] = None) -> str:
        """
        Get a prompt template and substitute variables.
        
        Args:
            prompt_name: Name of the prompt template
            data: Dictionary containing variables for substitution
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If required variables are missing
        """
        if prompt_name not in cls.PROMPTS:
            raise ValueError(f"Unknown prompt name: {prompt_name}")
        
        prompt_template = cls.PROMPTS[prompt_name]
        data = data or {}
        
        try:
            # Use str.format() for variable substitution
            formatted_prompt = prompt_template.format(**data)
            logger.info(f"Successfully formatted prompt '{prompt_name}' with data: {data}")
            return formatted_prompt
        except KeyError as e:
            missing_var = str(e).strip("'")
            error_msg = f"Missing required variable '{missing_var}' for prompt '{prompt_name}'"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error formatting prompt '{prompt_name}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @classmethod
    def validate_prompt_data(cls, prompt_name: PromptName, data: Dict[str, Any] = None) -> bool:
        """
        Validate that all required variables for a prompt are provided.
        
        Args:
            prompt_name: Name of the prompt template
            data: Dictionary containing variables for substitution
            
        Returns:
            True if validation passes
            
        Raises:
            ValueError: If validation fails
        """
        if prompt_name not in cls.PROMPTS:
            raise ValueError(f"Unknown prompt name: {prompt_name}")
        
        prompt_template = cls.PROMPTS[prompt_name]
        data = data or {}
        
        # Extract variable names from the template
        import re
        variable_pattern = r'\{(\w+)\}'
        required_vars = set(re.findall(variable_pattern, prompt_template))
        
        # Check if all required variables are provided
        missing_vars = required_vars - set(data.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables for prompt '{prompt_name}': {missing_vars}")
        
        return True
    
    @classmethod
    def list_available_prompts(cls) -> Dict[str, str]:
        """
        Get a list of all available prompt templates with descriptions.
        
        Returns:
            Dictionary mapping prompt names to descriptions
        """
        return {
            PromptName.COMPANY_ANALYSIS: "Analyze a company's market position, strengths, and opportunities",
            PromptName.TEXT_SUMMARY: "Provide comprehensive summaries of text content",
            PromptName.CODE_REVIEW: "Review code for quality, security, and best practices",
            PromptName.GENERAL_QUESTION: "Answer general questions with comprehensive responses"
        }
