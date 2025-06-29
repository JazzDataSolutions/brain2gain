"""
Email Template Service - MJML Template Compilation and Management
Part of Brain2Gain notification infrastructure

Handles:
- MJML template compilation to HTML
- Template data population with Jinja2
- Template caching and optimization
- Email template preview generation
- Integration with NotificationService
"""

import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for MJML email template compilation and management."""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "email-templates" / "src"
        self.cache_dir = Path(__file__).parent.parent / "email-templates" / "compiled"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Setup Jinja2 environment for data population
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml', 'mjml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.info(f"EmailTemplateService initialized with template dir: {self.template_dir}")

    async def compile_template(
        self, 
        template_name: str, 
        data: Dict[str, Any],
        force_recompile: bool = False
    ) -> str:
        """
        Compile MJML template to HTML with data population.
        
        Args:
            template_name: Name of the MJML template (without .mjml extension)
            data: Data to populate the template
            force_recompile: Force recompilation even if cached version exists
            
        Returns:
            Compiled HTML email content
        """
        try:
            mjml_file = self.template_dir / f"{template_name}.mjml"
            cache_file = self.cache_dir / f"{template_name}_{hash(str(data))}.html"
            
            if not mjml_file.exists():
                raise FileNotFoundError(f"Template not found: {template_name}.mjml")
            
            # Check if we have a cached version
            if not force_recompile and cache_file.exists():
                if cache_file.stat().st_mtime > mjml_file.stat().st_mtime:
                    logger.debug(f"Using cached template: {template_name}")
                    return cache_file.read_text(encoding='utf-8')
            
            # Load and populate MJML template with Jinja2
            template = self.jinja_env.get_template(f"{template_name}.mjml")
            populated_mjml = template.render(**data)
            
            # Compile MJML to HTML using MJML CLI
            html_content = await self._compile_mjml_to_html(populated_mjml)
            
            # Cache the compiled result
            cache_file.write_text(html_content, encoding='utf-8')
            
            logger.info(f"Template compiled successfully: {template_name}")
            return html_content
            
        except Exception as e:
            logger.error(f"Failed to compile template {template_name}: {e}")
            raise ValueError(f"Template compilation failed: {str(e)}")

    async def _compile_mjml_to_html(self, mjml_content: str) -> str:
        """
        Compile MJML content to HTML using MJML CLI.
        
        Args:
            mjml_content: MJML content string
            
        Returns:
            Compiled HTML content
        """
        try:
            # Create temporary file for MJML content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mjml', delete=False) as temp_file:
                temp_file.write(mjml_content)
                temp_file_path = temp_file.name
            
            try:
                # Try to compile with MJML CLI (if available)
                result = subprocess.run(
                    ['mjml', temp_file_path, '--stdout'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.warning(f"MJML CLI compilation failed: {result.stderr}")
                    # Fall back to basic HTML conversion
                    return await self._fallback_mjml_to_html(mjml_content)
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("MJML CLI not available, using fallback conversion")
                return await self._fallback_mjml_to_html(mjml_content)
                
        except Exception as e:
            logger.error(f"MJML compilation error: {e}")
            return await self._fallback_mjml_to_html(mjml_content)
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    async def _fallback_mjml_to_html(self, mjml_content: str) -> str:
        """
        Fallback MJML to HTML conversion when MJML CLI is not available.
        Provides basic conversion for development/testing.
        
        Args:
            mjml_content: MJML content string
            
        Returns:
            Basic HTML content
        """
        # Basic MJML to HTML conversion for fallback
        # This is a simplified conversion - in production, MJML CLI should be used
        html_content = mjml_content
        
        # Replace common MJML tags with HTML equivalents
        replacements = {
            '<mjml>': '<!DOCTYPE html><html>',
            '</mjml>': '</html>',
            '<mj-head>': '<head>',
            '</mj-head>': '</head>',
            '<mj-body': '<body',
            '</mj-body>': '</body>',
            '<mj-section': '<table width="100%" cellpadding="0" cellspacing="0"',
            '</mj-section>': '</table>',
            '<mj-column>': '<td>',
            '</mj-column>': '</td>',
            '<mj-text': '<div',
            '</mj-text>': '</div>',
            '<mj-button': '<a',
            '</mj-button>': '</a>',
            '<mj-image': '<img',
            '<mj-table>': '<table>',
            '</mj-table>': '</table>',
            '<mj-divider': '<hr',
            '<mj-social': '<div',
            '</mj-social>': '</div>',
            'background-color=': 'style="background-color:',
            'color=': 'style="color:',
            'font-size=': 'style="font-size:',
            'padding=': 'style="padding:',
            'align=': 'style="text-align:',
        }
        
        for mjml_tag, html_tag in replacements.items():
            html_content = html_content.replace(mjml_tag, html_tag)
        
        # Add basic email CSS
        html_content = html_content.replace(
            '<head>',
            '''<head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                    table { border-collapse: collapse; width: 100%; }
                    td { padding: 10px; }
                    .button { display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                </style>'''
        )
        
        logger.info("Used fallback MJML to HTML conversion")
        return html_content

    async def get_template_preview(self, template_name: str) -> str:
        """
        Generate preview HTML for a template with sample data.
        
        Args:
            template_name: Name of the template to preview
            
        Returns:
            HTML preview content
        """
        sample_data = self._get_sample_data(template_name)
        return await self.compile_template(template_name, sample_data)

    def _get_sample_data(self, template_name: str) -> Dict[str, Any]:
        """
        Get sample data for template preview.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Sample data dictionary
        """
        base_data = {
            "project_name": "Brain2Gain",
            "customer_name": "Juan Pérez",
            "order_id": "BG-2025-001234",
            "order_date": "28 de Junio, 2025",
            "total_amount": "89.99",
            "currency": "USD"
        }
        
        template_specific_data = {
            "order_confirmation": {
                **base_data,
                "payment_method": "Tarjeta de Crédito ****1234",
                "subtotal": "79.99",
                "shipping_cost": "10.00",
                "order_items": [
                    {
                        "product_name": "Proteína Whey Isolate 2kg",
                        "quantity": 1,
                        "unit_price": "49.99",
                        "total_price": "49.99"
                    },
                    {
                        "product_name": "Creatina Monohidrato 500g",
                        "quantity": 1,
                        "unit_price": "30.00",
                        "total_price": "30.00"
                    }
                ],
                "shipping_address": {
                    "full_name": "Juan Pérez",
                    "street": "Av. Revolución 123, Col. Centro",
                    "city": "Ciudad de México",
                    "state": "CDMX",
                    "zip_code": "06000",
                    "country": "México"
                },
                "track_order_url": "https://brain2gain.com/orders/BG-2025-001234"
            },
            
            "order_shipped": {
                **base_data,
                "tracking_number": "1Z999AA1234567890",
                "carrier_name": "FedEx",
                "shipped_date": "29 de Junio, 2025",
                "estimated_delivery": "1 de Julio, 2025",
                "tracking_url": "https://fedex.com/track?number=1Z999AA1234567890",
                "order_items": [
                    {
                        "product_name": "Proteína Whey Isolate 2kg",
                        "quantity": 1,
                        "total_price": "49.99"
                    },
                    {
                        "product_name": "Creatina Monohidrato 500g",
                        "quantity": 1,
                        "total_price": "30.00"
                    }
                ],
                "shipping_address": {
                    "full_name": "Juan Pérez",
                    "street": "Av. Revolución 123, Col. Centro",
                    "city": "Ciudad de México",
                    "state": "CDMX",
                    "zip_code": "06000",
                    "country": "México"
                }
            },
            
            "order_delivered": {
                **base_data,
                "delivered_date": "1 de Julio, 2025",
                "delivered_time": "14:30",
                "delivery_address": "Av. Revolución 123, Col. Centro, CDMX",
                "delivery_notes": "Entregado en recepción",
                "order_items": [
                    {
                        "product_name": "Proteína Whey Isolate 2kg",
                        "quantity": 1,
                        "total_price": "49.99"
                    },
                    {
                        "product_name": "Creatina Monohidrato 500g",
                        "quantity": 1,
                        "total_price": "30.00"
                    }
                ],
                "review_url": "https://brain2gain.com/review/BG-2025-001234",
                "reorder_url": "https://brain2gain.com/reorder/BG-2025-001234"
            },
            
            "reset_password": {
                "project_name": "Brain2Gain",
                "username": "juan.perez@email.com",
                "link": "https://brain2gain.com/reset-password?token=abc123def456",
                "valid_hours": "24"
            },
            
            "new_account": {
                "project_name": "Brain2Gain",
                "username": "juan.perez@email.com",
                "password": "TempPassword123!",
                "link": "https://brain2gain.com/dashboard"
            }
        }
        
        return template_specific_data.get(template_name, base_data)

    async def list_available_templates(self) -> list[str]:
        """
        List all available MJML templates.
        
        Returns:
            List of available template names (without .mjml extension)
        """
        try:
            templates = []
            for file_path in self.template_dir.glob("*.mjml"):
                templates.append(file_path.stem)
            
            logger.info(f"Found {len(templates)} templates: {templates}")
            return sorted(templates)
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    async def validate_template(self, template_name: str) -> Dict[str, Any]:
        """
        Validate template and return validation results.
        
        Args:
            template_name: Name of the template to validate
            
        Returns:
            Validation results
        """
        try:
            mjml_file = self.template_dir / f"{template_name}.mjml"
            
            if not mjml_file.exists():
                return {
                    "valid": False,
                    "errors": [f"Template file not found: {template_name}.mjml"]
                }
            
            # Try to compile with sample data
            sample_data = self._get_sample_data(template_name)
            await self.compile_template(template_name, sample_data)
            
            return {
                "valid": True,
                "template_name": template_name,
                "file_size": mjml_file.stat().st_size,
                "last_modified": datetime.fromtimestamp(mjml_file.stat().st_mtime).isoformat(),
                "errors": []
            }
            
        except Exception as e:
            return {
                "valid": False,
                "template_name": template_name,
                "errors": [str(e)]
            }

    async def clear_cache(self, template_name: str = None) -> bool:
        """
        Clear compiled template cache.
        
        Args:
            template_name: Specific template to clear (None for all)
            
        Returns:
            True if cache was cleared successfully
        """
        try:
            if template_name:
                # Clear specific template cache
                for cache_file in self.cache_dir.glob(f"{template_name}_*.html"):
                    cache_file.unlink()
                logger.info(f"Cleared cache for template: {template_name}")
            else:
                # Clear all cache
                for cache_file in self.cache_dir.glob("*.html"):
                    cache_file.unlink()
                logger.info("Cleared all template cache")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# Global email template service instance
email_template_service = EmailTemplateService()