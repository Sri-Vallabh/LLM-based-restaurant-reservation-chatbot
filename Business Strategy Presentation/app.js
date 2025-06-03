// Presentation JavaScript functionality

class Presentation {
    constructor() {
        this.currentSlide = 0;
        this.totalSlides = 15;
        this.slides = [];
        this.isFullscreen = false;
        
        this.init();
    }

    init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupPresentation());
        } else {
            this.setupPresentation();
        }
    }

    setupPresentation() {
        this.slides = document.querySelectorAll('.slide');
        console.log('Found slides:', this.slides.length);
        
        if (this.slides.length === 0) {
            console.error('No slides found!');
            return;
        }

        this.totalSlides = this.slides.length;
        this.bindEvents();
        this.showSlide(0);
        this.updateProgress();
        this.updateCounter();
        this.updateNavigationButtons();
    }

    bindEvents() {
        // Button controls
        const prevBtn = document.getElementById('prev-slide');
        const nextBtn = document.getElementById('next-slide');
        const fullscreenBtn = document.getElementById('fullscreen-toggle');

        if (prevBtn) prevBtn.addEventListener('click', () => this.previousSlide());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextSlide());
        if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());

        // Keyboard controls
        document.addEventListener('keydown', (e) => this.handleKeydown(e));

        // Fullscreen change events
        document.addEventListener('fullscreenchange', () => this.handleFullscreenChange());
        document.addEventListener('webkitfullscreenchange', () => this.handleFullscreenChange());
        document.addEventListener('mozfullscreenchange', () => this.handleFullscreenChange());
        document.addEventListener('msfullscreenchange', () => this.handleFullscreenChange());

        // Touch/swipe events for mobile
        this.addTouchEvents();

        console.log('Event listeners bound successfully');
    }

    handleKeydown(e) {
        switch(e.key) {
            case 'ArrowRight':
            case ' ':
            case 'Enter':
                e.preventDefault();
                this.nextSlide();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.previousSlide();
                break;
            case 'Home':
                e.preventDefault();
                this.goToSlide(0);
                break;
            case 'End':
                e.preventDefault();
                this.goToSlide(this.totalSlides - 1);
                break;
            case 'f':
            case 'F':
                if (!e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.toggleFullscreen();
                }
                break;
            case 'Escape':
                if (this.isFullscreen) {
                    this.exitFullscreen();
                }
                break;
        }
    }

    addTouchEvents() {
        let startX = 0;
        let startY = 0;
        const container = document.querySelector('.presentation-container');

        if (!container) return;

        container.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, { passive: true });

        container.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;

            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;

            const deltaX = startX - endX;
            const deltaY = startY - endY;

            // Only trigger if horizontal swipe is dominant and significant
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    this.nextSlide();
                } else {
                    this.previousSlide();
                }
            }

            startX = 0;
            startY = 0;
        }, { passive: true });
    }

    nextSlide() {
        if (this.currentSlide < this.totalSlides - 1) {
            this.goToSlide(this.currentSlide + 1);
        }
    }

    previousSlide() {
        if (this.currentSlide > 0) {
            this.goToSlide(this.currentSlide - 1);
        }
    }

    goToSlide(slideIndex) {
        if (slideIndex >= 0 && slideIndex < this.totalSlides) {
            console.log(`Going to slide ${slideIndex + 1}`);
            
            // Hide current slide
            this.hideAllSlides();
            
            // Update current slide index
            this.currentSlide = slideIndex;
            
            // Show new slide
            this.showSlide(slideIndex);
            
            // Update UI elements
            this.updateProgress();
            this.updateCounter();
            this.updateNavigationButtons();
            
            // Handle slide-specific logic
            this.handleSlideSpecifics(slideIndex);
        }
    }

    hideAllSlides() {
        this.slides.forEach(slide => {
            slide.classList.remove('active', 'animate-in');
        });
    }

    showSlide(index) {
        const slide = this.slides[index];
        if (slide) {
            // Remove active class from all slides first
            this.hideAllSlides();
            
            // Add active class to current slide
            slide.classList.add('active');
            
            // Add animation after a brief delay
            setTimeout(() => {
                slide.classList.add('animate-in');
                this.animateSlideContent(slide);
            }, 50);
        }
    }

    animateSlideContent(slide) {
        const elements = slide.querySelectorAll('.bullet-points li, .value-prop, .flow-step, .metric-category, .tech-component, .framework-item, .phase-card, .roi-metric, .challenge-category, .advantage, .timeline-item');
        
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, 100 + (index * 100));
        });
    }

    updateProgress() {
        const progressBar = document.querySelector('.progress-indicator');
        if (progressBar) {
            const progress = ((this.currentSlide + 1) / this.totalSlides) * 100;
            progressBar.style.width = `${progress}%`;
        }
    }

    updateCounter() {
        const currentSlideEl = document.getElementById('current-slide');
        const totalSlidesEl = document.getElementById('total-slides');
        
        if (currentSlideEl) currentSlideEl.textContent = this.currentSlide + 1;
        if (totalSlidesEl) totalSlidesEl.textContent = this.totalSlides;
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prev-slide');
        const nextBtn = document.getElementById('next-slide');

        if (prevBtn) {
            prevBtn.disabled = this.currentSlide === 0;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentSlide === this.totalSlides - 1;
            
            // Update button text for last slide
            if (this.currentSlide === this.totalSlides - 1) {
                nextBtn.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                `;
                nextBtn.setAttribute('aria-label', 'Finish presentation');
            } else {
                nextBtn.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                `;
                nextBtn.setAttribute('aria-label', 'Next slide');
            }
        }
    }

    toggleFullscreen() {
        if (!this.isFullscreen) {
            this.enterFullscreen();
        } else {
            this.exitFullscreen();
        }
    }

    enterFullscreen() {
        const container = document.querySelector('.presentation-container');
        
        if (container.requestFullscreen) {
            container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
        } else if (container.mozRequestFullScreen) {
            container.mozRequestFullScreen();
        } else if (container.msRequestFullscreen) {
            container.msRequestFullscreen();
        }
    }

    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }

    handleFullscreenChange() {
        const isFullscreen = !!(document.fullscreenElement || 
                              document.webkitFullscreenElement || 
                              document.mozFullScreenElement || 
                              document.msFullscreenElement);
        
        this.isFullscreen = isFullscreen;
        this.updateFullscreenIcon();
        
        const container = document.querySelector('.presentation-container');
        if (container) {
            if (isFullscreen) {
                container.classList.add('fullscreen');
            } else {
                container.classList.remove('fullscreen');
            }
        }
    }

    updateFullscreenIcon() {
        const icon = document.getElementById('fullscreen-icon');
        
        if (icon) {
            if (this.isFullscreen) {
                icon.innerHTML = `
                    <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
                `;
            } else {
                icon.innerHTML = `
                    <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                `;
            }
        }
    }

    // Method to handle special slide interactions
    initSlideInteractions() {
        // Add click handlers for call-to-action buttons
        const ctaButtons = document.querySelectorAll('.call-to-action .btn');
        ctaButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleCTAClick(button.textContent.trim());
            });
        });

        // Add hover effects for interactive elements
        this.addHoverEffects();
    }

    handleCTAClick(buttonText) {
        if (buttonText.includes('Schedule')) {
            this.showNotification('Meeting request sent! Check your calendar for confirmation.');
        } else if (buttonText.includes('Download')) {
            this.showNotification('Strategy document download initiated.');
        }
    }

    showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: var(--color-success);
            color: var(--color-btn-primary-text);
            padding: 16px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 1001;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    addHoverEffects() {
        // Add hover effects to interactive elements
        const interactiveElements = document.querySelectorAll('.value-prop, .tech-component, .framework-item, .advantage, .phase-card');
        
        interactiveElements.forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.style.transform = 'translateY(-5px)';
                element.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
                element.style.boxShadow = 'var(--shadow-lg)';
            });

            element.addEventListener('mouseleave', () => {
                element.style.transform = 'translateY(0)';
                element.style.boxShadow = '';
            });
        });
    }

    // Method to handle slide-specific logic
    handleSlideSpecifics(slideIndex) {
        switch(slideIndex) {
            case 0: // Title slide
                setTimeout(() => this.animateTitleSlide(), 500);
                break;
            case 5: // Customer journey flow
                setTimeout(() => this.animateFlowDiagram(), 500);
                break;
            case 11: // Business impact
                setTimeout(() => this.animateROIMetrics(), 500);
                break;
            case 14: // Conclusion
                setTimeout(() => this.initSlideInteractions(), 500);
                break;
        }
    }

    animateTitleSlide() {
        const highlights = document.querySelectorAll('.highlight');
        highlights.forEach((highlight, index) => {
            highlight.style.opacity = '0';
            highlight.style.transform = 'scale(0.8)';
            highlight.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                highlight.style.opacity = '1';
                highlight.style.transform = 'scale(1)';
            }, index * 200);
        });
    }

    animateFlowDiagram() {
        const steps = document.querySelectorAll('.flow-step');
        steps.forEach((step, index) => {
            step.style.opacity = '0';
            step.style.transform = 'translateX(-50px)';
            step.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                step.style.opacity = '1';
                step.style.transform = 'translateX(0)';
            }, index * 300);
        });
    }

    animateROIMetrics() {
        const metrics = document.querySelectorAll('.roi-metric h3');
        metrics.forEach((metric, index) => {
            const finalValue = metric.textContent;
            const isPercentage = finalValue.includes('%');
            const numericValue = parseInt(finalValue.replace(/[^\d]/g, ''));
            
            if (numericValue > 0) {
                metric.textContent = isPercentage ? '0%' : '0';
                
                setTimeout(() => {
                    this.animateNumber(metric, finalValue, numericValue, isPercentage);
                }, index * 200);
            }
        });
    }

    animateNumber(element, finalValue, numericValue, isPercentage) {
        let currentValue = 0;
        const increment = Math.ceil(numericValue / 30);
        
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= numericValue) {
                element.textContent = finalValue;
                clearInterval(timer);
            } else {
                element.textContent = isPercentage ? `${currentValue}%` : `${currentValue}`;
            }
        }, 50);
    }
}

// Initialize presentation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing presentation...');
    window.presentation = new Presentation();
});

// Fallback initialization for cases where DOMContentLoaded already fired
if (document.readyState !== 'loading') {
    console.log('DOM already loaded, initializing presentation...');
    window.presentation = new Presentation();
}

// Add global error handling
window.addEventListener('error', (e) => {
    console.error('Presentation error:', e.error);
});

// Add performance optimization
window.addEventListener('load', () => {
    console.log('Window loaded, optimizing...');
    // Preload images
    const images = document.querySelectorAll('img[src]');
    images.forEach(img => {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = img.src;
        document.head.appendChild(link);
    });
});

// Add visibility change handling for presentations
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pause any ongoing animations when tab is not visible
        document.querySelectorAll('.animate-in').forEach(el => {
            if (el.style.animationPlayState !== undefined) {
                el.style.animationPlayState = 'paused';
            }
        });
    } else {
        // Resume animations when tab becomes visible
        document.querySelectorAll('.animate-in').forEach(el => {
            if (el.style.animationPlayState !== undefined) {
                el.style.animationPlayState = 'running';
            }
        });
    }
});

// Export for potential external use
window.PresentationApp = Presentation;