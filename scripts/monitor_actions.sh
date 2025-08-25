#!/bin/bash

# Monitor GitHub Actions workflow runs
# Usage: ./monitor_actions.sh [workflow_name]

set -e

REPO_OWNER="ZhangYongguang5467"
REPO_NAME="pos-test"
WORKFLOW_NAME="${1:-build-and-push.yml}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=== GitHub Actions Monitor ==="
echo "Repository: $REPO_OWNER/$REPO_NAME"
echo "Workflow: $WORKFLOW_NAME"
echo ""

# Function to check if gh CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
        echo "Please install it from: https://cli.github.com/"
        exit 1
    fi
}

# Function to get latest workflow run
get_latest_run() {
    local workflow="$1"
    gh run list --workflow="$workflow" --limit=1 --json databaseId,status,conclusion,createdAt,headBranch,displayTitle --repo="$REPO_OWNER/$REPO_NAME" 2>/dev/null
}

# Function to get workflow run status
get_run_status() {
    local run_id="$1"
    gh run view "$run_id" --json status,conclusion,jobs --repo="$REPO_OWNER/$REPO_NAME" 2>/dev/null
}

# Function to get workflow run logs
get_run_logs() {
    local run_id="$1"
    echo -e "${BLUE}📋 Getting logs for run $run_id...${NC}"
    gh run view "$run_id" --log --repo="$REPO_OWNER/$REPO_NAME" 2>/dev/null
}

# Main monitoring function
monitor_workflow() {
    local workflow="$1"
    
    echo -e "${BLUE}🔍 Checking latest workflow run...${NC}"
    
    local run_info
    run_info=$(get_latest_run "$workflow")
    
    if [ -z "$run_info" ]; then
        echo -e "${YELLOW}⚠️  No workflow runs found for: $workflow${NC}"
        return 1
    fi
    
    local run_id=$(echo "$run_info" | jq -r '.[0].databaseId')
    local status=$(echo "$run_info" | jq -r '.[0].status')
    local conclusion=$(echo "$run_info" | jq -r '.[0].conclusion')
    local created_at=$(echo "$run_info" | jq -r '.[0].createdAt')
    local branch=$(echo "$run_info" | jq -r '.[0].headBranch')
    local title=$(echo "$run_info" | jq -r '.[0].displayTitle')
    
    echo "📊 Latest Run Information:"
    echo "  ID: $run_id"
    echo "  Title: $title"
    echo "  Branch: $branch"
    echo "  Created: $created_at"
    echo "  Status: $status"
    echo "  Conclusion: $conclusion"
    echo ""
    
    # Show status with colors
    case "$status" in
        "in_progress")
            echo -e "${YELLOW}🔄 Workflow is running...${NC}"
            ;;
        "completed")
            if [ "$conclusion" = "success" ]; then
                echo -e "${GREEN}✅ Workflow completed successfully!${NC}"
            elif [ "$conclusion" = "failure" ]; then
                echo -e "${RED}❌ Workflow failed!${NC}"
                echo ""
                echo -e "${RED}💥 Failure Details:${NC}"
                get_run_logs "$run_id" | tail -50
            elif [ "$conclusion" = "cancelled" ]; then
                echo -e "${YELLOW}⏹️  Workflow was cancelled${NC}"
            else
                echo -e "${YELLOW}⚠️  Workflow completed with conclusion: $conclusion${NC}"
            fi
            ;;
        *)
            echo -e "${YELLOW}❓ Unknown status: $status${NC}"
            ;;
    esac
    
    return 0
}

# Main execution
main() {
    check_gh_cli
    
    if ! monitor_workflow "$WORKFLOW_NAME"; then
        echo -e "${RED}❌ Failed to monitor workflow${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}🔗 View in browser:${NC}"
    echo "https://github.com/$REPO_OWNER/$REPO_NAME/actions"
}

main "$@"