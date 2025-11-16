<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* Material Design 3 Colors */
  --md-primary: #FF8C00;
  --md-primary-variant: #FFD700;
  --md-surface: #FFFFFF;
  --md-surface-variant: #F5F5F5;
  --md-background: #FAFAFA;
  --md-on-surface: #1C1B1F;
  --md-on-surface-variant: #49454F;
  --md-outline: #79747E;
  --md-shadow: rgba(0, 0, 0, 0.15);
  
  /* Elevation shadows */
  --md-elevation-1: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  --md-elevation-2: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
  --md-elevation-3: 0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23);
  --md-elevation-4: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
  
  /* Typography */
  --md-font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Oxygen, Ubuntu, Cantarell, sans-serif;
  --md-headline-size: 1.5rem;
  --md-title-size: 1.25rem;
  --md-body-size: 1rem;
  --md-label-size: 0.875rem;
  
  /* Spacing */
  --md-spacing-xs: 0.25rem;
  --md-spacing-sm: 0.5rem;
  --md-spacing-md: 1rem;
  --md-spacing-lg: 1.5rem;
  --md-spacing-xl: 2rem;
  
  /* Border radius */
  --md-radius-sm: 8px;
  --md-radius-md: 12px;
  --md-radius-lg: 16px;
  --md-radius-xl: 24px;
}

body {
  font-family: var(--md-font-family);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: var(--md-background);
  color: var(--md-on-surface);
  line-height: 1.5;
}

#app {
  min-height: 100vh;
}

/* Material Design transitions */
.material-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>

