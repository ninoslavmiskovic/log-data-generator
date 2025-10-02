# Screenshots for Log Data Generator Web UI

This directory contains screenshots referenced in the main README.md file. 

## Required Screenshots

To complete the documentation, please add the following screenshots:

### 1. `dashboard-overview.png`
- **What to capture:** Main dashboard page at http://localhost:8080
- **Key elements:** Navigation bar, welcome cards, current configuration panel, features list
- **Description:** Shows the clean, modern interface and main entry points

### 2. `data-type-selection.png`
- **What to capture:** Generate page showing the data type selection grid at http://localhost:8080/generate
- **Key elements:** 8 data type cards with icons, selected state, and interactive hover effects
- **Description:** Shows the comprehensive data type selection interface

### 3. `configuration-screen.png`
- **What to capture:** Settings page at http://localhost:8080/config
- **Key elements:** Elasticsearch config, Kibana config, log generation settings, test connections button
- **Description:** Demonstrates the easy-to-use configuration interface

### 4. `settings-flow.png`
- **What to capture:** Settings page with connection test results visible
- **Key elements:** Filled-in configuration forms, test connection results showing success/failure
- **Description:** Shows the step-by-step configuration process

### 5. `generation-process.png`
- **What to capture:** Progress page during log generation at http://localhost:8080/progress/[operation-id]
- **Key elements:** Progress bar, status messages, timeline of operations
- **Description:** Real-time progress tracking interface

### 6. `kibana-integration.png`
- **What to capture:** Kibana Discover page showing the pre-built saved searches
- **Key elements:** Discover sessions list, one of the ES|QL queries, data preview
- **Description:** Shows the automatically created Kibana objects

### 7. `discover-sessions.png`
- **What to capture:** Kibana showing one of the DISSECT or GROK parsing examples
- **Key elements:** ES|QL query with parsing, results showing extracted fields
- **Description:** Demonstrates the advanced parsing capabilities

### 8. `configuration-options.png`
- **What to capture:** Settings page showing all configuration sections expanded
- **Key elements:** All form fields visible, help text, validation messages
- **Description:** Comprehensive view of all available settings

### 9. `progress-tracking.png`
- **What to capture:** Progress page showing completed operation with timeline
- **Key elements:** 100% progress bar, success message, timeline of all steps, action buttons
- **Description:** Shows successful completion of the generation process

## How to Take Screenshots

1. **Launch the application:**
   ```bash
   cd /path/to/log-data-generator
   source venv/bin/activate
   python app.py
   ```

2. **Open browser:** Navigate to http://localhost:8080

3. **Take screenshots:** Use your browser's screenshot tools or system screenshot utility

4. **Optimize images:** 
   - Use PNG format for crisp UI elements
   - Compress images to keep file sizes reasonable
   - Ensure text is readable at different zoom levels

5. **Name files exactly as shown above** to match the README references

## Screenshot Guidelines

- **Resolution:** Use high-resolution screenshots (1920x1080 or higher)
- **Browser:** Use a modern browser (Chrome, Firefox, Safari) for best rendering
- **Window size:** Use a standard desktop window size, not mobile/tablet
- **Content:** Show realistic data, not empty states
- **Annotations:** Consider adding subtle arrows or highlights for key features
- **Consistency:** Use the same browser and zoom level for all screenshots

## Alternative: Demo GIFs

Consider creating animated GIFs for dynamic processes:
- `log-generation-flow.gif` - Complete process from configuration to completion
- `connection-testing.gif` - Testing connections and seeing results
- `kibana-setup.gif` - Showing the automatically created Kibana objects

## Notes

- Screenshots are referenced in README.md with relative paths
- Update this file if you add new screenshots or change the documentation
- Consider creating both light and dark theme versions if applicable
- Test that all screenshot references in README.md work correctly
