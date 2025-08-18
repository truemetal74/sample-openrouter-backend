from typing import Dict, Any
from app.models import PromptName
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages server-stored prompt templates with variable substitution."""
    
    # Server-stored prompt templates with descriptions
    PROMPTS = {
        PromptName.COMPANY_ANALYSIS: {
            "template": """
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
            "description": "Analyze a company's market position, strengths, and opportunities"
        },
        
        PromptName.TEXT_SUMMARY: {
            "template": """
Please provide a comprehensive summary of the following text:

Text: {text}

Requirements:
- Maintain key information and context
- Highlight main points and conclusions
- Keep the summary concise but informative
- Preserve the original tone and style where appropriate
""",
            "description": "Provide comprehensive summaries of text content"
        },
        
        PromptName.CODE_REVIEW: {
            "template": """
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
            "description": "Review code for quality, security, and best practices"
        },
        
        PromptName.GENERAL_QUESTION: {
            "template": """
Please answer the following question:

Question: {question}

Additional Context: {context if context else 'None provided'}

Please provide a comprehensive and accurate answer based on the information provided.
""",
            "description": "Answer general questions with comprehensive responses"
        }
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
        
        prompt_data = cls.PROMPTS[prompt_name]
        prompt_template = prompt_data["template"]
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
        
        prompt_data = cls.PROMPTS[prompt_name]
        prompt_template = prompt_data["template"]
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
            name: data["description"] 
            for name, data in cls.PROMPTS.items()
        }
    
    @classmethod
    def add_prompt(cls, prompt_name: str, prompt_template: str, description: str = None) -> bool:
        """
        Add a new prompt template dynamically.
        
        Args:
            prompt_name: Name of the new prompt template
            prompt_template: The prompt template string with variable placeholders
            description: Optional description of the prompt template
            
        Returns:
            True if prompt was added successfully, False otherwise
            
        Raises:
            ValueError: If prompt_name already exists or template is invalid
        """
        try:
            # Check if prompt already exists
            if prompt_name in cls.PROMPTS:
                raise ValueError(f"Prompt '{prompt_name}' already exists")
            
            # Validate template format (basic check for variable placeholders)
            import re
            variable_pattern = r'\{(\w+)\}'
            variables = re.findall(variable_pattern, prompt_template)
            
            if not variables:
                logger.warning(f"Prompt template '{prompt_name}' has no variable placeholders")
            
            # Add the new prompt
            cls.PROMPTS[prompt_name] = {
                "template": prompt_template,
                "description": description or f"Custom prompt template: {prompt_name}"
            }
            
            # Log the addition
            logger.info(f"Added new prompt template '{prompt_name}' with {len(variables)} variables: {variables}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error adding prompt '{prompt_name}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @classmethod
    def remove_prompt(cls, prompt_name: str) -> bool:
        """
        Remove a prompt template.
        
        Args:
            prompt_name: Name of the prompt template to remove
            
        Returns:
            True if prompt was removed successfully, False otherwise
            
        Raises:
            ValueError: If prompt_name doesn't exist or is a built-in prompt
        """
        try:
            # Check if prompt exists
            if prompt_name not in cls.PROMPTS:
                raise ValueError(f"Prompt '{prompt_name}' does not exist")
            
            # Prevent removal of built-in prompts
            built_in_prompts = {PromptName.COMPANY_ANALYSIS, PromptName.TEXT_SUMMARY, 
                               PromptName.CODE_REVIEW, PromptName.GENERAL_QUESTION}
            
            if prompt_name in built_in_prompts:
                raise ValueError(f"Cannot remove built-in prompt '{prompt_name}'")
            
            # Remove the prompt
            removed_template = cls.PROMPTS.pop(prompt_name)
            
            # Log the removal
            logger.info(f"Removed prompt template '{prompt_name}'")
            
            return True
            
        except Exception as e:
            error_msg = f"Error removing prompt '{prompt_name}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @classmethod
    def update_prompt(cls, prompt_name: str, new_template: str, new_description: str = None) -> bool:
        """
        Update an existing prompt template.
        
        Args:
            prompt_name: Name of the prompt template to update
            new_template: The new prompt template string
            new_description: Optional new description
            
        Returns:
            True if prompt was updated successfully, False otherwise
            
        Raises:
            ValueError: If prompt_name doesn't exist or template is invalid
        """
        try:
            # Check if prompt exists
            if prompt_name not in cls.PROMPTS:
                raise ValueError(f"Prompt '{prompt_name}' does not exist")
            
            # Validate new template format
            import re
            variable_pattern = r'\{(\w+)\}'
            variables = re.findall(variable_pattern, new_template)
            
            if not variables:
                logger.warning(f"Updated prompt template '{prompt_name}' has no variable placeholders")
            
            # Store old template for logging
            old_template = cls.PROMPTS[prompt_name]["template"]
            
            # Update the prompt
            cls.PROMPTS[prompt_name] = {
                "template": new_template,
                "description": new_description or cls.PROMPTS[prompt_name].get("description", f"Custom prompt template: {prompt_name}")
            }
            
            # Log the update
            logger.info(f"Updated prompt template '{prompt_name}' with {len(variables)} variables: {variables}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error updating prompt '{prompt_name}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @classmethod
    def get_prompt_info(cls, prompt_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a prompt template.
        
        Args:
            prompt_name: Name of the prompt template
            
        Returns:
            Dictionary containing prompt information
            
        Raises:
            ValueError: If prompt_name doesn't exist
        """
        if prompt_name not in cls.PROMPTS:
            raise ValueError(f"Prompt '{prompt_name}' does not exist")
        
        prompt_data = cls.PROMPTS[prompt_name]
        template = prompt_data["template"]
        
        # Extract variables from template
        import re
        variable_pattern = r'\{(\w+)\}'
        variables = re.findall(variable_pattern, template)
        
        # Determine if it's a built-in prompt
        built_in_prompts = {PromptName.COMPANY_ANALYSIS, PromptName.TEXT_SUMMARY, 
                           PromptName.CODE_REVIEW, PromptName.GENERAL_QUESTION}
        is_built_in = prompt_name in built_in_prompts
        
        return {
            "name": prompt_name,
            "template": template,
            "variables": variables,
            "variable_count": len(variables),
            "is_built_in": is_built_in,
            "description": prompt_data.get("description", "No description available")
        }
