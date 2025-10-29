# Troubleshooting Guide

This guide helps you resolve common issues when using ComfyFixerSmart. If you encounter a problem not covered here, check the logs and consider opening an issue on GitHub.

## Quick Diagnosis

### Check Your Setup

Run this diagnostic command to verify your configuration:

```bash
comfyfixer --validate-config --log-level DEBUG
```

This will check:
- Configuration file validity
- ComfyUI installation path
- API key accessibility
- Directory permissions

### Common Symptoms and Solutions

## Configuration Issues

### "CIVITAI_API_KEY not found"

**Symptoms:**
```
Error: CIVITAI_API_KEY environment variable not set
Error: Civitai API key not found in ~/.secrets
```

**Solutions:**

1. **Get API Key:**
   - Visit https://civitai.com/user/account
   - Generate a new API key
   - Copy the key

2. **Set via Environment Variable:**
   ```bash
   export CIVITAI_API_KEY="your-api-key-here"
   # Add to ~/.bashrc for persistence
   echo 'export CIVITAI_API_KEY="your-key"' >> ~/.bashrc
   ```

3. **Set via Secrets File:**
   ```bash
   echo "CIVITAI_API_KEY=your-api-key-here" >> ~/.secrets
   chmod 600 ~/.secrets  # Secure permissions
   ```

4. **Test the key:**
   ```bash
   curl -H "Authorization: Bearer $CIVITAI_API_KEY" https://civitai.com/api/v1/models?limit=1
   ```

### "ComfyUI root directory not found"

**Symptoms:**
```
Error: comfyui_root is not a valid directory: /path/to/comfyui
Configuration Error: ComfyUI installation not found
```

**Solutions:**

1. **Verify ComfyUI Installation:**
   ```bash
   ls -la /path/to/comfyui
   # Should see: main.py, requirements.txt, models/, user/, etc.
   ```

2. **Update Configuration:**
   ```toml
   # config/default.toml
   comfyui_root = "/correct/path/to/ComfyUI-stable"
   ```

3. **Set Environment Variable:**
   ```bash
   export COMFYUI_ROOT="/correct/path/to/ComfyUI-stable"
   ```

4. **Check via Command Line:**
   ```bash
   comfyfixer --comfyui-root /correct/path/to/ComfyUI-stable --validate-config
   ```

### "Configuration file not found"

**Symptoms:**
```
Error: Configuration file not found: config/default.toml
```

**Solutions:**

1. **Create Default Configuration:**
   ```bash
   mkdir -p config
   cat > config/default.toml << 'EOF'
   comfyui_root = "/path/to/comfyui"
   workflow_dirs = ["user/default/workflows"]
   search_backends = ["civitai"]
   EOF
   ```

2. **Use Custom Config Path:**
   ```bash
   comfyfixer --config /path/to/your/config.toml
   ```

3. **Check Current Directory:**
   ```bash
   pwd  # Should be ComfyFixerSmart root
   ls -la config/
   ```

## Workflow Analysis Issues

### "No workflows found"

**Symptoms:**
```
Warning: No workflow files found in search paths
Info: Scanned directories: /path/to/workflows
Result: 0 workflows analyzed
```

**Solutions:**

1. **Check Workflow Directory:**
   ```bash
   ls -la /path/to/comfyui/user/default/workflows/
   # Should see .json files
   ```

2. **Verify File Extensions:**
   ```bash
   find /path/to/workflows -name "*.json" | head -5
   ```

3. **Check Permissions:**
   ```bash
   ls -ld /path/to/workflows
   # Should be readable
   ```

4. **Update Configuration:**
   ```toml
   workflow_dirs = [
       "user/default/workflows",
       "custom/workflows"
   ]
   ```

5. **Use Command Line:**
   ```bash
   comfyfixer --dir /path/to/workflows
   ```

### "Invalid workflow format"

**Symptoms:**
```
Error: Failed to parse workflow: workflow.json
Error: Invalid JSON format
Warning: Skipping malformed workflow
```

**Solutions:**

1. **Validate JSON:**
   ```bash
   python -m json.tool workflow.json
   # Should output formatted JSON
   ```

2. **Check File Encoding:**
   ```bash
   file workflow.json
   # Should be UTF-8
   ```

3. **Fix Common Issues:**
   - Remove trailing commas
   - Ensure proper quote escaping
   - Check for special characters

4. **Use ComfyUI to Validate:**
   - Load the workflow in ComfyUI
   - Save it again to fix formatting

## Search and Download Issues

### "Model not found on Civitai"

**Symptoms:**
```
Warning: Model 'model_name.safetensors' not found on Civitai
Info: Searched with query: model_name
Result: No matches found
```

**Solutions:**

1. **Check Model Name:**
   - Verify the filename in the workflow
   - Try searching manually on Civitai

2. **Use Fuzzy Search:**
   - ComfyFixerSmart uses fuzzy matching
   - Check logs for alternative names tried

3. **Try Different Backend:**
   ```bash
   comfyfixer --search huggingface
   ```

4. **Manual Search:**
   - Visit https://civitai.com/models
   - Search for the model name
   - Note the correct filename

### "Download failed"

**Symptoms:**
```
Error: Download failed for model_name.safetensors
Error: Connection timeout
Error: HTTP 404 Not Found
```

**Solutions:**

1. **Check Network Connection:**
   ```bash
   ping civitai.com
   curl -I https://civitai.com
   ```

2. **Verify API Key:**
   ```bash
   # Test API access
   curl -H "Authorization: Bearer $CIVITAI_API_KEY" \
        "https://civitai.com/api/v1/models?limit=1"
   ```

3. **Check Disk Space:**
   ```bash
   df -h
   du -sh /path/to/models/
   ```

4. **Manual Download:**
   - Use the generated script: `bash output/download_missing.sh`
   - Or download directly from Civitai

5. **Resume Downloads:**
   ```bash
   comfyfixer --resume
   ```

### "Permission denied"

**Symptoms:**
```
Error: Permission denied: /path/to/models/
Error: Cannot create directory
```

**Solutions:**

1. **Check Directory Permissions:**
   ```bash
   ls -ld /path/to/comfyui/models/
   # Should be writable by current user
   ```

2. **Fix Permissions:**
   ```bash
   chmod -R u+w /path/to/comfyui/models/
   # Or change ownership
   sudo chown -R $USER:$USER /path/to/comfyui/
   ```

3. **Use sudo (not recommended):**
   ```bash
   sudo comfyfixer  # Not recommended for security
   ```

## Performance Issues

### "Out of memory"

**Symptoms:**
```
Error: MemoryError
Warning: High memory usage detected
Process killed due to memory limit
```

**Solutions:**

1. **Reduce Concurrency:**
   ```bash
   comfyfixer --concurrency 1
   ```

2. **Process Fewer Workflows:**
   ```bash
   comfyfixer specific_workflow.json
   ```

3. **Increase System Memory:**
   - Close other applications
   - Add swap space if needed

4. **Monitor Memory:**
   ```bash
   # During run
   watch -n 1 'ps aux | grep comfyfixer'
   ```

### "Slow performance"

**Symptoms:**
- Searches take longer than expected
- Downloads are slow
- Overall execution time is high

**Solutions:**

1. **Check Network Speed:**
   ```bash
   speedtest-cli
   ```

2. **Enable Caching:**
   ```toml
   cache_enabled = true
   cache_ttl_hours = 24
   ```

3. **Increase Timeouts:**
   ```bash
   comfyfixer --download-timeout 600
   ```

4. **Use Faster Backend:**
   ```bash
   comfyfixer --search huggingface
   ```

## API and Rate Limiting Issues

### "API rate limit exceeded"

**Symptoms:**
```
Error: HTTP 429 Too Many Requests
Warning: Rate limit hit, waiting...
```

**Solutions:**

1. **Wait and Retry:**
   - ComfyFixerSmart automatically waits
   - Default delay: 60 seconds

2. **Reduce Request Frequency:**
   ```toml
   civitai_rate_limit_delay = 2.0
   ```

3. **Use Cache:**
   ```toml
   cache_enabled = true
   ```

### "API authentication failed"

**Symptoms:**
```
Error: HTTP 401 Unauthorized
Error: Invalid API key
```

**Solutions:**

1. **Verify API Key:**
   ```bash
   # Test with curl
   curl -H "Authorization: Bearer $CIVITAI_API_KEY" \
        https://civitai.com/api/v1/models?limit=1
   ```

2. **Check Key Format:**
   - Should be 64 characters
   - No extra spaces or characters

3. **Regenerate Key:**
   - Old keys may expire
   - Create new key on Civitai

## File System Issues

### "Disk full"

**Symptoms:**
```
Error: No space left on device
Error: Write failed
```

**Solutions:**

1. **Check Disk Space:**
   ```bash
   df -h
   du -sh /path/to/comfyui/models/
   ```

2. **Clean Up Space:**
   ```bash
   # Remove old logs
   rm -f logs/*.log.old.*
   # Clean temp files
   rm -rf /tmp/comfyfixer_*
   ```

3. **Change Output Directory:**
   ```bash
   comfyfixer --output-dir /path/with/more/space
   ```

### "File locked or busy"

**Symptoms:**
```
Error: File is locked
Error: Resource temporarily unavailable
```

**Solutions:**

1. **Check for Running Processes:**
   ```bash
   lsof /path/to/file
   ps aux | grep comfyfixer
   ```

2. **Wait and Retry:**
   - Close other ComfyUI instances
   - Wait for downloads to complete

3. **Force Unlock (Linux):**
   ```bash
   fuser -k /path/to/file  # Careful!
   ```

## Logging and Debugging

### Enable Debug Logging

```bash
comfyfixer --log-level DEBUG --verbose --log-file debug.log
```

### Check Logs

```bash
# View recent logs
tail -f logs/comfyfixer_*.log

# Search for errors
grep -i error logs/*.log

# Check specific run
ls -la logs/
cat logs/comfyfixer_20241201_120000.log
```

### Common Log Messages

**Successful Operation:**
```
INFO: Analysis complete: 15 workflows, 3 missing models
INFO: Download complete: model.safetensors
```

**Warnings:**
```
WARNING: Model not found: model_name.safetensors
WARNING: Cache miss for query: model_name
```

**Errors:**
```
ERROR: API request failed: Connection timeout
ERROR: Download failed: HTTP 404
```

## Getting Help

### Self-Help Steps

1. **Update ComfyFixerSmart:**
   ```bash
   pip install -U comfyfixersmart
   ```

2. **Check Documentation:**
   ```bash
   # Local docs
   cat docs/README.md
   # Online: https://github.com/username/comfyfixersmart
   ```

3. **Run Diagnostics:**
   ```bash
   comfyfixer --validate-config --verbose
   ```

### Community Support

1. **GitHub Issues:**
   - Search existing issues
   - Create new issue with logs

2. **Include Debug Info:**
   ```bash
   # System info
   python --version
   pip list | grep comfyfixer

   # Configuration (redact API keys)
   cat config/default.toml

   # Error logs
   tail -50 logs/comfyfixer_*.log
   ```

### Professional Support

For enterprise support or custom development:
- Contact the maintainers
- Check for commercial support options

## Prevention

### Best Practices

1. **Regular Backups:**
   ```bash
   cp -r /path/to/comfyui/models/ /path/to/backup/
   ```

2. **Monitor Disk Space:**
   ```bash
   # Add to cron
   */30 * * * * df -h / | grep -v Use%
   ```

3. **Keep API Keys Secure:**
   ```bash
   chmod 600 ~/.secrets
   ```

4. **Update Regularly:**
   ```bash
   pip install -U comfyfixersmart
   ```

5. **Test Configurations:**
   ```bash
   comfyfixer --validate-config
   ```

### Monitoring

Set up monitoring for long-running operations:

```bash
# Monitor progress
watch -n 30 'ls -la output/ | grep download'

# Check for errors
tail -f logs/comfyfixer_*.log | grep -i error
```

This proactive approach helps catch issues early.