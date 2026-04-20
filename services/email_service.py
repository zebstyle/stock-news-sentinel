"""
Email Service
Handles sending email notifications for stock alerts
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
from datetime import datetime

from utils.logger import LoggerMixin
from utils.config import Config


class EmailService(LoggerMixin):
    """Sends email notifications for stock alerts"""
    
    def __init__(self, config: Config):
        """
        Initialize email service
        
        Args:
            config: Configuration instance
        """
        self.config = config
    
    def _create_alert_email(self, article: Dict[str, Any], sentiment: Dict[str, Any]) -> str:
        """
        Create HTML email content for an alert
        
        Args:
            article: Article data
            sentiment: Sentiment analysis result
            
        Returns:
            HTML email content
        """
        stock = article.get('stock', 'Unknown')
        title = article.get('title', 'No title')
        url = article.get('url', '#')
        text = article.get('text', '')
        
        sentiment_score = sentiment.get('sentiment_score', 0)
        sentiment_label = sentiment.get('sentiment_label', 'neutral')
        confidence = sentiment.get('confidence', 0)
        
        # Determine color based on sentiment
        if sentiment_label == 'positive':
            color = '#28a745'
            emoji = '📈'
        elif sentiment_label == 'negative':
            color = '#dc3545'
            emoji = '📉'
        else:
            color = '#6c757d'
            emoji = '➡️'
        
        # Create snippet
        snippet = text[:self.config.snippet_max_length] + '...' if len(text) > self.config.snippet_max_length else text
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: {color};
                    color: white;
                    padding: 20px;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border: 1px solid #dee2e6;
                }}
                .footer {{
                    background-color: #e9ecef;
                    padding: 15px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                    border-radius: 0 0 5px 5px;
                }}
                .metric {{
                    display: inline-block;
                    margin: 10px 15px 10px 0;
                }}
                .metric-label {{
                    font-weight: bold;
                    color: #6c757d;
                }}
                .metric-value {{
                    font-size: 18px;
                    color: {color};
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: {color};
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 15px;
                }}
                .snippet {{
                    background-color: white;
                    padding: 15px;
                    border-left: 4px solid {color};
                    margin: 15px 0;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{emoji} Stock Alert: {stock}</h2>
                    <p style="margin: 0;">Significant news detected</p>
                </div>
                <div class="content">
                    <h3>{title}</h3>
                    
                    <div class="metric">
                        <span class="metric-label">Sentiment:</span>
                        <span class="metric-value">{sentiment_label.upper()}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Score:</span>
                        <span class="metric-value">{sentiment_score:.2f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Confidence:</span>
                        <span class="metric-value">{confidence:.1%}</span>
                    </div>
                    
                    {f'<div class="snippet">{snippet}</div>' if self.config.include_article_snippet else ''}
                    
                    <a href="{url}" class="button">Read Full Article</a>
                    
                    <p style="margin-top: 20px; font-size: 12px; color: #6c757d;">
                        Analyzed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
                <div class="footer">
                    <p>Stock News Sentinel - Automated Stock News Monitoring</p>
                    <p>This is an automated alert. Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_summary_email(self, articles: List[Dict[str, Any]]) -> str:
        """
        Create HTML email content for daily summary
        
        Args:
            articles: List of articles with sentiment data
            
        Returns:
            HTML email content
        """
        positive_count = sum(1 for a in articles if a.get('sentiment_label') == 'positive')
        negative_count = sum(1 for a in articles if a.get('sentiment_label') == 'negative')
        neutral_count = sum(1 for a in articles if a.get('sentiment_label') == 'neutral')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 700px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 5px 5px 0 0;
                    text-align: center;
                }}
                .stats {{
                    display: flex;
                    justify-content: space-around;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .stat-box {{
                    text-align: center;
                    padding: 15px;
                }}
                .stat-number {{
                    font-size: 32px;
                    font-weight: bold;
                }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .neutral {{ color: #6c757d; }}
                .article-item {{
                    background-color: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 4px solid #667eea;
                    border-radius: 3px;
                }}
                .footer {{
                    background-color: #e9ecef;
                    padding: 15px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                    border-radius: 0 0 5px 5px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Stock News Summary</h1>
                    <p>{datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number positive">{positive_count}</div>
                        <div>Positive</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number negative">{negative_count}</div>
                        <div>Negative</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number neutral">{neutral_count}</div>
                        <div>Neutral</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{len(articles)}</div>
                        <div>Total Articles</div>
                    </div>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Top Articles</h2>
        """
        
        # Add top articles
        for article in articles[:10]:  # Top 10 articles
            stock = article.get('stock', 'Unknown')
            title = article.get('title', 'No title')
            url = article.get('url', '#')
            sentiment_label = article.get('sentiment_label', 'neutral')
            sentiment_score = article.get('sentiment_score', 0)
            
            sentiment_class = sentiment_label if sentiment_label in ['positive', 'negative', 'neutral'] else 'neutral'
            
            html += f"""
                    <div class="article-item">
                        <strong class="{sentiment_class}">[{stock}]</strong> {title}
                        <br>
                        <small>Sentiment: {sentiment_label.upper()} ({sentiment_score:.2f})</small>
                        <br>
                        <a href="{url}" style="font-size: 12px;">Read article →</a>
                    </div>
            """
        
        html += """
                </div>
                
                <div class="footer">
                    <p>Stock News Sentinel - Automated Stock News Monitoring</p>
                    <p>This is an automated summary. Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_alert(self, article: Dict[str, Any], sentiment: Dict[str, Any]) -> bool:
        """
        Send email alert for a single article
        
        Args:
            article: Article data
            sentiment: Sentiment analysis result
            
        Returns:
            True if email sent successfully
        """
        try:
            stock = article.get('stock', 'Unknown')
            sentiment_label = sentiment.get('sentiment_label', 'neutral')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{self.config.email_subject_prefix} {sentiment_label.upper()} news for {stock}"
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            
            # Create HTML content
            html_content = self._create_alert_email(article, sentiment)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_from, self.config.email_password)
                server.send_message(msg)
            
            self.logger.info(f"Alert email sent for {stock}: {article.get('title', '')[:50]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending alert email: {e}")
            return False
    
    def send_daily_summary(self, articles: List[Dict[str, Any]]) -> bool:
        """
        Send daily summary email
        
        Args:
            articles: List of articles with sentiment data
            
        Returns:
            True if email sent successfully
        """
        try:
            if not articles:
                self.logger.info("No articles to include in daily summary")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{self.config.email_subject_prefix} Daily Summary - {len(articles)} articles"
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            
            # Create HTML content
            html_content = self._create_summary_email(articles)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_from, self.config.email_password)
                server.send_message(msg)
            
            self.logger.info(f"Daily summary email sent with {len(articles)} articles")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary email: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test email connection
        
        Returns:
            True if connection successful
        """
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_from, self.config.email_password)
            
            self.logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Email connection test failed: {e}")
            return False


# Made with Bob