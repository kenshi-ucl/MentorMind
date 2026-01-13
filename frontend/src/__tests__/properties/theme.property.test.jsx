/**
 * Feature: mentormind-ai-tutor, Property 4: Theme Toggle Round-Trip
 * Validates: Requirements 3.5
 * 
 * For any initial theme state, toggling the theme twice should return 
 * the application to the original theme state.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import * as fc from 'fast-check'
import { ThemeProvider, useTheme, THEME_KEY } from '../../context/ThemeContext'

describe('Property 4: Theme Toggle Round-Trip', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    // Reset document class
    document.documentElement.classList.remove('dark')
  })

  it('toggling theme twice returns to original state for any initial theme', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('light', 'dark'),
        (initialTheme) => {
          // Setup: Set initial theme in localStorage
          localStorage.setItem(THEME_KEY, initialTheme)
          
          // Render the hook with ThemeProvider
          const wrapper = ({ children }) => <ThemeProvider>{children}</ThemeProvider>
          const { result } = renderHook(() => useTheme(), { wrapper })
          
          // Verify initial state
          expect(result.current.theme).toBe(initialTheme)
          
          // Toggle once
          act(() => {
            result.current.toggleTheme()
          })
          
          // Should be opposite
          const afterFirstToggle = result.current.theme
          expect(afterFirstToggle).toBe(initialTheme === 'light' ? 'dark' : 'light')
          
          // Toggle again
          act(() => {
            result.current.toggleTheme()
          })
          
          // Should be back to original
          expect(result.current.theme).toBe(initialTheme)
          
          // Cleanup for next iteration
          localStorage.clear()
          document.documentElement.classList.remove('dark')
        }
      ),
      { numRuns: 100 }
    )
  })
})
