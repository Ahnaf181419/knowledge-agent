# Troubleshooting

## Common Issues

### Installation Issues

#### Playwright Installation Fails

**Symptom**: `playwright install` fails or times out

**Solution**:
```bash
# Install dependencies first
uv pip install -r requirements.txt

# Then install playwright browsers
playwright install chromium
# or for all browsers
playwright install
```

#### Module Not Found Errors

**Symptom**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```bash
# Reinstall dependencies
uv pip install -r requirements.txt
```

### Scraping Issues

#### All Methods Fail

**Symptom**: All scraping methods fail for a URL

**Possible Causes**:
1. Website is down
2. Website blocks all scraping attempts
3. Network issues

**Solution**:
1. Check if the website is accessible in browser
2. Try with VPN/Proxy
3. Add to retry queue for later
4. Try CloudScraper engine for Cloudflare-protected sites

#### Playwright Timeout

**Symptom**: Playwright times out waiting for page

**Solution**:
```python
# Increase timeout in settings
state.set_setting('retry_count', 3)

# Or modify runner.py timeout values
```

#### Cloudflare Block

**Symptom**: Cloudflare challenge page returned

**Solution**:
1. Use CloudScraper engine
2. Wait and retry (Cloudflare challenges are transient)
3. Use a proxy

#### Duplicate Content Detected

**Symptom**: Content marked as duplicate

**Possible Causes**:
1. Exact content already scraped (SHA256 match)
2. Similar content from same domain (BM25 match)

**Solution**:
```python
# Adjust similarity threshold
state.set_setting('bm25_similarity_threshold', 0.9)  # More lenient
```

### Performance Issues

#### High Memory Usage

**Symptom**: Application uses too much memory

**Solution**:
```python
# Reduce concurrent jobs
state.set_setting('concurrent_jobs', 1)

# Clear old data periodically
# Delete old entries from database
```

#### Slow Scraping

**Symptom**: Scraping is very slow

**Solutions**:
1. Reduce retry count
2. Disable robots.txt checking (less safe)
3. Use simpler extraction methods

#### UI Freezes

**Symptom**: Gradio interface becomes unresponsive

**Solution**:
1. Reduce concurrent jobs
2. Clear browser cache
3. Restart the application

### Queue and State Issues

#### Queue Not Saving

**Symptom**: Queue resets on restart

**Solution**:
```python
# Check auto_save is enabled
state.set_setting('auto_save_queue', True)

# Manually save
state.save_queue()
```

#### Settings Not Persisting

**Symptom**: Settings revert to defaults

**Solution**:
```python
# Check settings file permissions
# Ensure settings.json is writable

# Manually save
state.save_settings()
```

### Notification Issues

#### Notifications Not Working

**Symptom**: No system notifications

**Solutions**:
1. Enable notifications in settings
2. Check OS notification permissions
3. Check notification service is running

### Data Issues

#### Database Issues

**Symptom**: Application crashes or errors on startup

**Solution**:
1. Backup current database
2. Delete corrupted file (will be recreated)
3. Restore from backup if available

```bash
# Backup
cp knowledge.db knowledge.db.bak

# Recreate (careful - loses data)
rm knowledge.db
```

#### History Not Updating

**Symptom**: Extracted URLs don't appear in history

**Solution**:
1. Check file permissions
2. Check disk space
3. Check logs for errors

### Error Messages

#### "No content extracted"

**Cause**: Page loaded but no text content found

**Solution**:
1. Try different scraping method
2. Check if page requires login
3. Verify URL is correct

#### "Failed to fetch HTML"

**Cause**: Network error or blocking

**Solution**:
1. Check internet connection
2. Try with VPN
3. Use alternative method

#### "robots.txt forbids scraping"

**Cause**: Site robots.txt blocks scraping

**Solution**:
```python
# Disable robots.txt checking (not recommended)
state.set_setting('respect_robots_txt', False)
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs

Logs are stored in `logs/scraper_YYYYMMDD.log`

### Test Individual Components

```python
# Test scraper engine
from scraper.engines import SimpleHTTPEngine
engine = SimpleHTTPEngine()
result = engine.scrape("https://example.com")
print(result)

# Test validator
from utils.validators import is_valid_url
print(is_valid_url("https://example.com"))
```

## Getting Help

1. Check existing GitHub issues
2. Search documentation
3. Open new issue with:
   - Python version
   - Operating system
   - Error message
   - Steps to reproduce
   - Relevant logs

## Known Limitations

1. Cannot scrape sites requiring login (without cookies)
2. Cannot bypass paid paywalls
3. Some sites may block all automated access
4. Large files may take time to process
5. Network-dependent (offline = no scraping)

## Performance Tips

1. Use batch processing for multiple URLs
2. Set appropriate concurrent job limit
3. Clear completed items from queue
4. Regular maintenance of database
5. Monitor system resources
