// Mobile-specific JavaScript for TimeTracker

class MobileEnhancer {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.init();
    }

    init() {
        this.detectMobile();
        this.enhanceTouchTargets();
        this.enhanceTables();
        this.enhanceNavigation();
        this.enhanceModals();
        this.enhanceForms();
        this.addTouchGestures();
        this.handleViewportChanges();
        this.addMobileSpecificFeatures();
    }

    detectMobile() {
        if (this.isMobile) {
            document.body.classList.add('mobile-view');
            this.addMobileMetaTags();
        }
    }

    addMobileMetaTags() {
        // Add mobile-specific meta tags if not already present
        if (!document.querySelector('meta[name="mobile-web-app-capable"]')) {
            const meta = document.createElement('meta');
            meta.name = 'mobile-web-app-capable';
            meta.content = 'yes';
            document.head.appendChild(meta);
        }

        if (!document.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
            const meta = document.createElement('meta');
            meta.name = 'apple-mobile-web-app-capable';
            meta.content = 'yes';
            document.head.appendChild(meta);
        }
    }

    enhanceTouchTargets() {
        // Improve touch targets for mobile
        const touchElements = document.querySelectorAll('.btn, .form-control, .form-select, .nav-link, .dropdown-item');
        touchElements.forEach(element => {
            element.classList.add('touch-target');
            
            // Add touch feedback
            element.addEventListener('touchstart', this.handleTouchStart.bind(this));
            element.addEventListener('touchend', this.handleTouchEnd.bind(this));
        });
    }

    // Add missing touch event handlers
    handleTouchStart(event) {
        const element = event.currentTarget;
        element.style.transform = 'scale(0.98)';
        element.style.transition = 'transform 0.1s ease';
        
        // Store touch coordinates for gesture detection
        this.touchStartX = event.touches[0].clientX;
        this.touchStartY = event.touches[0].clientY;
    }

    handleTouchEnd(event) {
        const element = event.currentTarget;
        element.style.transform = 'scale(1)';
        
        // Store end coordinates for gesture detection
        this.touchEndX = event.changedTouches[0].clientX;
        this.touchEndY = event.changedTouches[0].clientY;
    }

    enhanceTables() {
        if (!this.isMobile) return;

        const tables = document.querySelectorAll('.table');
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    // Add data-label attributes for mobile table display
                    const header = table.querySelector(`thead th:nth-child(${index + 1})`);
                    if (header) {
                        cell.setAttribute('data-label', header.textContent.trim());
                    }
                });
            });
        });
    }

    enhanceNavigation() {
        if (!this.isMobile) return;

        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');

        if (navbarToggler && navbarCollapse) {
            // Close mobile menu when clicking outside
            document.addEventListener('click', (event) => {
                const isClickInsideNavbar = navbarToggler.contains(event.target) || navbarCollapse.contains(event.target);
                
                if (!isClickInsideNavbar && navbarCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                    bsCollapse.hide();
                }
            });

            // Close mobile menu when clicking on a nav link
            const navLinks = navbarCollapse.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    if (window.innerWidth <= 991.98) {
                        const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                        bsCollapse.hide();
                    }
                });
            });

            // Add swipe to close functionality
            this.addSwipeToClose(navbarCollapse);
        }
    }

    enhanceModals() {
        if (!this.isMobile) return;

        // Enhance modal behavior on mobile
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            // Add swipe to close functionality
            this.addSwipeToClose(modal);
            
            // Improve modal positioning
            modal.addEventListener('shown.bs.modal', () => {
                this.centerModal(modal);
            });
        });
    }

    enhanceForms() {
        if (!this.isMobile) return;

        // Enhance form inputs for mobile
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.classList.add('mobile-form');
            
            // Add mobile-specific form validation
            this.addMobileFormValidation(form);
            
            // Improve form submission on mobile
            this.enhanceFormSubmission(form);
        });
    }

    addTouchGestures() {
        if (!this.isMobile) return;

        // Add swipe gestures for navigation
        this.addSwipeNavigation();
        
        // Add pull-to-refresh functionality
        this.addPullToRefresh();
        
        // Add touch feedback
        this.addTouchFeedback();
    }

    addSwipeToClose(element) {
        let startX = 0;
        let startY = 0;
        let currentX = 0;
        let currentY = 0;

        element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        element.addEventListener('touchmove', (e) => {
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
            
            const diffX = startX - currentX;
            const diffY = startY - currentY;
            
            // Horizontal swipe to close
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (element.classList.contains('navbar-collapse')) {
                    const bsCollapse = new bootstrap.Collapse(element);
                    bsCollapse.hide();
                } else if (element.classList.contains('modal')) {
                    const modal = bootstrap.Modal.getInstance(element);
                    if (modal) modal.hide();
                }
            }
        });
    }

    addSwipeNavigation() {
        let startX = 0;
        let startY = 0;

        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        document.addEventListener('touchend', (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Swipe left/right for navigation (if on specific pages)
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 100) {
                this.handleSwipeNavigation(diffX > 0 ? 'left' : 'right');
            }
        });
    }

    addPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let pullDistance = 0;
        let isPulling = false;

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        });

        document.addEventListener('touchmove', (e) => {
            if (!isPulling) return;
            
            currentY = e.touches[0].clientY;
            pullDistance = currentY - startY;
            
            if (pullDistance > 0 && pullDistance < 100) {
                this.showPullToRefreshIndicator(pullDistance);
            }
        });

        document.addEventListener('touchend', () => {
            if (isPulling && pullDistance > 80) {
                this.refreshPage();
            }
            this.hidePullToRefreshIndicator();
            isPulling = false;
        });
    }

    addTouchFeedback() {
        const touchElements = document.querySelectorAll('.btn, .card, .nav-link');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', () => {
                element.style.transform = 'scale(0.98)';
                element.style.transition = 'transform 0.1s ease';
            });
            
            element.addEventListener('touchend', () => {
                element.style.transform = 'scale(1)';
            });
        });
    }

    handleSwipeNavigation(direction) {
        // Handle swipe navigation based on current page
        const currentPath = window.location.pathname;
        
        if (direction === 'left') {
            // Swipe left - go forward
            if (window.history.length > 1) {
                window.history.forward();
            }
        } else {
            // Swipe right - go back
            if (window.history.length > 1) {
                window.history.back();
            }
        }
    }

    showPullToRefreshIndicator(distance) {
        // Create or update pull-to-refresh indicator
        let indicator = document.getElementById('pull-to-refresh-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'pull-to-refresh-indicator';
            indicator.innerHTML = `
                <div class="text-center p-3">
                    <i class="fas fa-arrow-down text-primary"></i>
                    <span class="ms-2">Pull to refresh</span>
                </div>
            `;
            indicator.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: white;
                z-index: 9999;
                transform: translateY(-100%);
                transition: transform 0.3s ease;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            `;
            document.body.appendChild(indicator);
        }
        
        const translateY = Math.min(distance * 0.5, 100);
        indicator.style.transform = `translateY(${translateY - 100}px)`;
    }

    hidePullToRefreshIndicator() {
        const indicator = document.getElementById('pull-to-refresh-indicator');
        if (indicator) {
            indicator.style.transform = 'translateY(-100%)';
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 300);
        }
    }

    refreshPage() {
        // Show loading indicator
        this.showLoadingIndicator();
        
        // Refresh the page
        setTimeout(() => {
            window.location.reload();
        }, 500);
    }

    showLoadingIndicator() {
        const loading = document.createElement('div');
        loading.id = 'mobile-loading-indicator';
        loading.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-2">Refreshing...</div>
            </div>
        `;
        loading.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 10000;
        `;
        document.body.appendChild(loading);
    }

    centerModal(modal) {
        // Center modal content on mobile
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.margin = 'auto';
            modalContent.style.maxHeight = '90vh';
            modalContent.style.overflow = 'auto';
        }
    }

    addMobileFormValidation(form) {
        // Add mobile-specific form validation
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('invalid', (e) => {
                e.preventDefault();
                this.showMobileValidationError(input);
            });
            
            input.addEventListener('input', () => {
                this.hideMobileValidationError(input);
            });
        });
    }

    showMobileValidationError(input) {
        // Show mobile-friendly validation error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'mobile-validation-error';
        errorDiv.textContent = input.validationMessage;
        errorDiv.style.cssText = `
            color: #dc2626;
            font-size: 0.875rem;
            margin-top: 0.25rem;
            padding: 0.5rem;
            background: #fef2f2;
            border-radius: 6px;
            border: 1px solid #fecaca;
        `;
        
        input.parentNode.appendChild(errorDiv);
        input.style.borderColor = '#dc2626';
    }

    hideMobileValidationError(input) {
        const errorDiv = input.parentNode.querySelector('.mobile-validation-error');
        if (errorDiv) {
            errorDiv.remove();
        }
        input.style.borderColor = '#e2e8f0';
    }

    enhanceFormSubmission(form) {
        // Enhance form submission for mobile
        form.addEventListener('submit', (e) => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div>Submitting...';
                submitBtn.disabled = true;
            }
        });
    }

    handleViewportChanges() {
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;
            
            if (wasMobile !== this.isMobile) {
                if (this.isMobile) {
                    document.body.classList.add('mobile-view');
                    this.enhanceTouchTargets();
                    this.enhanceTables();
                } else {
                    document.body.classList.remove('mobile-view');
                }
            }
        });
    }

    addMobileSpecificFeatures() {
        if (!this.isMobile) return;

        // Add mobile-specific features
        this.addMobileKeyboardHandling();
        this.addMobileScrollOptimization();
        this.addMobilePerformanceOptimizations();
    }

    addMobileKeyboardHandling() {
        // Handle mobile keyboard events
        const inputs = document.querySelectorAll('input, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                // Scroll to input when focused on mobile
                setTimeout(() => {
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            });
        });
    }

    addMobileScrollOptimization() {
        // Optimize scrolling on mobile
        let ticking = false;
        
        const updateScroll = () => {
            // Add scroll-based animations or effects
            ticking = false;
        };
        
        const requestTick = () => {
            if (!ticking) {
                requestAnimationFrame(updateScroll);
                ticking = true;
            }
        };
        
        document.addEventListener('scroll', requestTick, { passive: true });
    }

    addMobilePerformanceOptimizations() {
        // Add mobile-specific performance optimizations
        
        // Lazy load images
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
        
        // Optimize animations for mobile
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        if (prefersReducedMotion.matches) {
            document.body.style.setProperty('--transition', 'none');
        }
    }
}

// Initialize mobile enhancements when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MobileEnhancer();
});

// Export for use in other scripts
window.MobileEnhancer = MobileEnhancer;
