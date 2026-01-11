"""
TerraJinki Orchestrator Agent

Master coordinator that plans, delegates to swarms, synthesizes results,
and manages human-in-the-loop approval gates.

The Orchestrator is the brain of TerraJinki, using Claude Opus for
strategic reasoning and coordination.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable, Awaitable
from uuid import uuid4
import asyncio
import json
import logging

from terrajinki.core.types import (
    Parcel,
    SiteAnalysis,
    SiteScore,
    AgentResult,
    SwarmResult,
    AgentStatus,
    ApprovalGate,
    ApprovalLevel,
    HumanDecision,
    ProjectType,
)
from terrajinki.agents.base import (
    BaseAgent,
    AgentContext,
    CompositeAgent,
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Request for site analysis."""
    parcel: Parcel
    project_type: ProjectType = ProjectType.UTILITY_SOLAR
    target_capacity_mw: float = 0.0  # 0 = auto-calculate
    include_financial: bool = True
    priority: str = "normal"  # low, normal, high, urgent
    requester_id: str = ""
    notes: str = ""


@dataclass
class AnalysisPlan:
    """Execution plan created by orchestrator."""
    id: str = field(default_factory=lambda: str(uuid4()))
    request: Optional[AnalysisRequest] = None

    # Planned swarms
    swarms_to_execute: List[str] = field(default_factory=list)
    execution_order: str = "parallel"  # parallel, sequential, hybrid

    # Estimated resources
    estimated_duration_seconds: float = 60.0
    estimated_cost: float = 0.50
    estimated_tokens: int = 10000

    # Special handling
    requires_satellite: bool = False
    requires_gnn: bool = False
    requires_rag: bool = True

    # Approval prediction
    likely_approval_gates: List[str] = field(default_factory=list)


class OrchestratorAgent(CompositeAgent[AnalysisRequest, SiteAnalysis]):
    """
    Master orchestrator for TerraJinki site analysis.

    Responsibilities:
    1. Receives analysis requests
    2. Creates execution plans
    3. Dispatches to specialized swarms
    4. Synthesizes results
    5. Manages human approval gates
    6. Generates recommendations

    Uses Claude Opus for strategic reasoning.
    """

    name = "orchestrator"
    description = "Master coordinator for renewable energy site analysis"
    model_tier = "orchestrator"
    default_approval_level = ApprovalLevel.AUTONOMOUS

    # Swarm registry
    SWARM_REGISTRY: Dict[str, type] = {}  # Populated by swarm imports

    def __init__(self, context: Optional[AgentContext] = None):
        super().__init__(context)
        self._swarms: Dict[str, Any] = {}
        self._initialize_swarms()

    def _initialize_swarms(self):
        """Initialize available swarms."""
        # Import swarms dynamically to avoid circular imports
        try:
            from terrajinki.agents.swarms.permitting import PermittingSwarm
            from terrajinki.agents.swarms.grid import GridSwarm
            from terrajinki.agents.swarms.environmental import EnvironmentalSwarm
            from terrajinki.agents.swarms.land import LandSwarm

            self._swarms = {
                "permitting": PermittingSwarm(self.context),
                "grid": GridSwarm(self.context),
                "environmental": EnvironmentalSwarm(self.context),
                "land": LandSwarm(self.context),
            }
        except ImportError as e:
            logger.warning(f"Some swarms not available: {e}")
            # Create placeholder swarms
            self._swarms = {}

    async def execute(self, request: AnalysisRequest) -> SiteAnalysis:
        """
        Execute comprehensive site analysis.

        Flow:
        1. Plan the analysis
        2. Execute swarms in parallel
        3. Aggregate results
        4. Calculate scores
        5. Check approval gates
        6. Generate recommendations
        """
        analysis = SiteAnalysis(
            parcel_id=request.parcel.id,
            project_type=request.project_type,
            requested_at=datetime.utcnow(),
        )

        await self.report_progress(0.1, "Planning analysis...")

        # Step 1: Create execution plan
        plan = await self._create_plan(request)

        await self.report_progress(0.2, f"Executing {len(plan.swarms_to_execute)} analysis swarms...")

        # Step 2: Execute swarms
        swarm_results = await self._execute_swarms(request, plan)

        await self.report_progress(0.7, "Aggregating results...")

        # Step 3: Aggregate results into analysis
        analysis = await self._aggregate_results(analysis, swarm_results)

        await self.report_progress(0.8, "Calculating scores...")

        # Step 4: Calculate overall scores
        analysis.score = await self._calculate_scores(analysis, swarm_results)

        await self.report_progress(0.9, "Generating recommendations...")

        # Step 5: Check for approval requirements
        approval_gates = await self._check_approval_gates(analysis)
        if approval_gates:
            analysis.requires_human_review = True
            analysis.review_reasons = [g.description for g in approval_gates]

            # Request human decisions
            for gate in approval_gates:
                if self.context.on_approval_required:
                    decision = await self.context.on_approval_required(
                        gate, {"analysis": analysis}
                    )
                    if decision:
                        analysis.human_decision = decision

        # Step 6: Generate recommendations
        analysis = await self._generate_recommendations(analysis)

        # Finalize
        analysis.completed_at = datetime.utcnow()
        analysis.duration_seconds = (
            analysis.completed_at - analysis.requested_at
        ).total_seconds()

        await self.report_progress(1.0, "Analysis complete")

        return analysis

    async def _create_plan(self, request: AnalysisRequest) -> AnalysisPlan:
        """
        Create execution plan using LLM reasoning.

        Analyzes the request to determine:
        - Which swarms to execute
        - Execution order
        - Resource estimates
        - Potential approval gates
        """
        prompt = f"""Analyze this site analysis request and create an execution plan.

PARCEL INFORMATION:
- State: {request.parcel.state}
- County: {request.parcel.county}
- Acreage: {request.parcel.acreage}
- Zoning: {request.parcel.zoning_type.value if request.parcel.zoning_type else 'unknown'}
- Current solar permission: {request.parcel.solar_permission.value if request.parcel.solar_permission else 'unknown'}
- Distance to substation: {request.parcel.nearest_substation_mi} miles

PROJECT TYPE: {request.project_type.value}
TARGET CAPACITY: {request.target_capacity_mw} MW (0 = auto-calculate)

Available analysis swarms:
1. permitting - Zoning ordinance analysis, permit requirements
2. grid - Interconnection analysis, substation capacity, queue
3. environmental - Wetlands, flood zones, species, farmland
4. land - Topography, ownership, access, value

Determine:
1. Which swarms are needed (all are recommended for comprehensive analysis)
2. Execution order: "parallel" (fastest), "sequential" (dependent), or "hybrid"
3. Whether satellite imagery analysis is needed
4. Whether GNN grid analysis should be used
5. Potential approval gates that might be triggered

Respond in JSON format:
{{
    "swarms_to_execute": ["permitting", "grid", "environmental", "land"],
    "execution_order": "parallel",
    "requires_satellite": true/false,
    "requires_gnn": true/false,
    "estimated_duration_seconds": 60,
    "likely_approval_gates": ["gate_name if applicable"],
    "reasoning": "Brief explanation of plan"
}}"""

        response = await self.call_llm(prompt, json_mode=True)

        return AnalysisPlan(
            request=request,
            swarms_to_execute=response.get("swarms_to_execute", ["permitting", "grid", "environmental", "land"]),
            execution_order=response.get("execution_order", "parallel"),
            requires_satellite=response.get("requires_satellite", False),
            requires_gnn=response.get("requires_gnn", False),
            estimated_duration_seconds=response.get("estimated_duration_seconds", 60),
            likely_approval_gates=response.get("likely_approval_gates", []),
        )

    async def _execute_swarms(
        self,
        request: AnalysisRequest,
        plan: AnalysisPlan,
    ) -> Dict[str, SwarmResult]:
        """Execute swarms according to plan."""
        results: Dict[str, SwarmResult] = {}

        if plan.execution_order == "parallel":
            # Execute all swarms in parallel
            tasks = {}
            for swarm_name in plan.swarms_to_execute:
                if swarm_name in self._swarms:
                    swarm = self._swarms[swarm_name]
                    tasks[swarm_name] = asyncio.create_task(
                        swarm.run(request)
                    )

            for swarm_name, task in tasks.items():
                try:
                    result = await asyncio.wait_for(
                        task,
                        timeout=self.context.config.agents.swarm_timeout_seconds
                    )
                    results[swarm_name] = result
                except asyncio.TimeoutError:
                    logger.error(f"Swarm {swarm_name} timed out")
                    results[swarm_name] = SwarmResult(
                        swarm_type=swarm_name,
                        status=AgentStatus.FAILED,
                        key_findings=["Swarm timed out"],
                    )
                except Exception as e:
                    logger.exception(f"Swarm {swarm_name} failed: {e}")
                    results[swarm_name] = SwarmResult(
                        swarm_type=swarm_name,
                        status=AgentStatus.FAILED,
                        key_findings=[f"Error: {str(e)}"],
                    )

        elif plan.execution_order == "sequential":
            # Execute swarms one at a time
            for swarm_name in plan.swarms_to_execute:
                if swarm_name in self._swarms:
                    try:
                        result = await self._swarms[swarm_name].run(request)
                        results[swarm_name] = result
                    except Exception as e:
                        logger.exception(f"Swarm {swarm_name} failed: {e}")
                        results[swarm_name] = SwarmResult(
                            swarm_type=swarm_name,
                            status=AgentStatus.FAILED,
                        )

        else:  # hybrid
            # First execute critical swarms, then others in parallel
            critical = ["permitting", "grid"]
            secondary = ["environmental", "land"]

            for swarm_name in critical:
                if swarm_name in self._swarms and swarm_name in plan.swarms_to_execute:
                    try:
                        result = await self._swarms[swarm_name].run(request)
                        results[swarm_name] = result
                    except Exception as e:
                        results[swarm_name] = SwarmResult(
                            swarm_type=swarm_name,
                            status=AgentStatus.FAILED,
                        )

            # Execute secondary in parallel
            tasks = {}
            for swarm_name in secondary:
                if swarm_name in self._swarms and swarm_name in plan.swarms_to_execute:
                    tasks[swarm_name] = asyncio.create_task(
                        self._swarms[swarm_name].run(request)
                    )

            for swarm_name, task in tasks.items():
                try:
                    results[swarm_name] = await task
                except Exception as e:
                    results[swarm_name] = SwarmResult(
                        swarm_type=swarm_name,
                        status=AgentStatus.FAILED,
                    )

        return results

    async def _aggregate_results(
        self,
        analysis: SiteAnalysis,
        swarm_results: Dict[str, SwarmResult],
    ) -> SiteAnalysis:
        """Aggregate swarm results into unified analysis."""
        # Track which agents executed
        analysis.agents_executed = list(swarm_results.keys())
        analysis.agent_durations = {
            name: (r.completed_at - r.started_at).total_seconds() if r.completed_at else 0
            for name, r in swarm_results.items()
        }

        # Extract component analyses from swarm outputs
        if "permitting" in swarm_results:
            result = swarm_results["permitting"]
            if result.agent_results:
                # Get jurisdiction from permitting swarm
                for ar in result.agent_results:
                    if ar.output.get("jurisdiction"):
                        from terrajinki.core.types import Jurisdiction
                        # Would deserialize here
                        pass

        if "grid" in swarm_results:
            result = swarm_results["grid"]
            # Extract grid analysis

        if "environmental" in swarm_results:
            result = swarm_results["environmental"]
            # Extract environmental screening

        return analysis

    async def _calculate_scores(
        self,
        analysis: SiteAnalysis,
        swarm_results: Dict[str, SwarmResult],
    ) -> SiteScore:
        """Calculate comprehensive site scores."""
        config = self.context.config.scoring

        score = SiteScore(
            parcel_id=analysis.parcel_id,
            scored_at=datetime.utcnow(),
            permitting_weight=config.permitting_weight,
            grid_weight=config.grid_weight,
            environmental_weight=config.environmental_weight,
            land_weight=config.land_weight,
            financial_weight=config.financial_weight,
        )

        # Extract scores from swarm results
        for swarm_name, result in swarm_results.items():
            if result.status == AgentStatus.COMPLETED:
                swarm_score = result.overall_score

                if swarm_name == "permitting":
                    score.permitting_score = swarm_score
                elif swarm_name == "grid":
                    score.grid_score = swarm_score
                elif swarm_name == "environmental":
                    score.environmental_score = swarm_score
                elif swarm_name == "land":
                    score.land_score = swarm_score

                # Collect risks
                score.major_risks.extend(result.risks)

        # Calculate overall score
        score.calculate_overall()

        # Identify fatal flaws
        fatal_conditions = config.fatal_flaw_conditions
        for result in swarm_results.values():
            for finding in result.key_findings:
                for condition in fatal_conditions:
                    if condition.lower() in finding.lower():
                        score.fatal_flaws.append(finding)

        # Calculate confidence based on data completeness
        completed_swarms = sum(
            1 for r in swarm_results.values()
            if r.status == AgentStatus.COMPLETED
        )
        score.data_completeness = completed_swarms / max(len(swarm_results), 1)
        score.confidence = sum(r.confidence for r in swarm_results.values()) / max(len(swarm_results), 1)

        return score

    async def _check_approval_gates(
        self,
        analysis: SiteAnalysis,
    ) -> List[ApprovalGate]:
        """Determine if human approval is required."""
        gates = []
        config = self.context.config.agents

        if not analysis.score:
            return gates

        # Fatal flaw gate
        if analysis.score.fatal_flaws:
            gates.append(ApprovalGate(
                name="fatal_flaw_confirmation",
                description=f"Fatal flaws detected: {', '.join(analysis.score.fatal_flaws[:3])}",
                level=ApprovalLevel.APPROVE,
                trigger_conditions=analysis.score.fatal_flaws,
            ))

        # Low score gate
        if analysis.score.overall_score < config.fatal_flaw_score_threshold:
            gates.append(ApprovalGate(
                name="low_score_review",
                description=f"Site score {analysis.score.overall_score:.1f} below threshold",
                level=ApprovalLevel.APPROVE,
                score_threshold=config.fatal_flaw_score_threshold,
            ))

        # High value gate
        if analysis.score.overall_score > config.high_value_score_threshold:
            gates.append(ApprovalGate(
                name="high_value_opportunity",
                description=f"High-value site detected (score {analysis.score.overall_score:.1f})",
                level=ApprovalLevel.NOTIFY,
                score_threshold=config.high_value_score_threshold,
            ))

        # Cost threshold gate
        if analysis.estimated_development_cost > config.cost_approval_threshold:
            gates.append(ApprovalGate(
                name="high_cost_review",
                description=f"Development cost ${analysis.estimated_development_cost:,.0f} exceeds threshold",
                level=ApprovalLevel.APPROVE,
                cost_threshold=config.cost_approval_threshold,
            ))

        return gates

    async def _generate_recommendations(self, analysis: SiteAnalysis) -> SiteAnalysis:
        """Generate actionable recommendations using LLM."""
        if not analysis.score:
            analysis.proceed_recommendation = "insufficient_data"
            analysis.recommended_next_steps = ["Complete site analysis"]
            return analysis

        prompt = f"""Based on this site analysis, provide recommendations.

SITE SCORE: {analysis.score.overall_score:.1f}/100 ({analysis.score.viability})
- Permitting: {analysis.score.permitting_score:.1f}
- Grid: {analysis.score.grid_score:.1f}
- Environmental: {analysis.score.environmental_score:.1f}
- Land: {analysis.score.land_score:.1f}

FATAL FLAWS: {analysis.score.fatal_flaws or 'None'}
MAJOR RISKS: {analysis.score.major_risks[:5] or 'None identified'}

Provide:
1. proceed_recommendation: "proceed", "proceed_with_caution", or "do_not_proceed"
2. Up to 5 prioritized next steps
3. Estimated development timeline in months
4. Key opportunities to highlight

Respond in JSON:
{{
    "proceed_recommendation": "proceed|proceed_with_caution|do_not_proceed",
    "next_steps": ["step 1", "step 2", ...],
    "estimated_months": 24,
    "opportunities": ["opportunity 1", ...]
}}"""

        response = await self.call_llm(prompt, json_mode=True)

        analysis.proceed_recommendation = response.get("proceed_recommendation", "proceed_with_caution")
        analysis.recommended_next_steps = response.get("next_steps", [])
        analysis.estimated_development_months = response.get("estimated_months", 24)
        analysis.score.opportunities = response.get("opportunities", [])

        return analysis

    async def quick_score(self, parcel: Parcel) -> Dict[str, Any]:
        """
        Quick preliminary scoring without full analysis.

        Useful for rapid screening of many parcels.
        """
        prompt = f"""Provide a quick preliminary score for this parcel.

PARCEL:
- Location: {parcel.county}, {parcel.state}
- Acreage: {parcel.acreage}
- Zoning: {parcel.zoning_type.value if parcel.zoning_type else 'unknown'}
- Solar permission: {parcel.solar_permission.value if parcel.solar_permission else 'unknown'}
- Distance to substation: {parcel.nearest_substation_mi} miles

Score from 0-100 based on:
- Zoning favorability for solar
- Acreage (typically need 5-7 acres per MW)
- Grid proximity

Respond in JSON:
{{
    "quick_score": 0-100,
    "confidence": 0.0-1.0,
    "key_factors": ["factor 1", "factor 2"],
    "recommendation": "worth_analyzing|skip|needs_more_info"
}}"""

        return await self.call_llm(prompt, json_mode=True, model=self.context.config.llm.anthropic_model_fast)


class WorkflowEngine:
    """
    Manages complex multi-step workflows with persistence and resumption.

    For long-running analyses that may span multiple sessions or
    require human intervention.
    """

    def __init__(self, context: AgentContext):
        self.context = context
        self.orchestrator = OrchestratorAgent(context)
        self._active_workflows: Dict[str, Dict] = {}

    async def start_workflow(
        self,
        workflow_type: str,
        request: AnalysisRequest,
    ) -> str:
        """Start a new workflow and return workflow ID."""
        workflow_id = str(uuid4())

        self._active_workflows[workflow_id] = {
            "id": workflow_id,
            "type": workflow_type,
            "request": request,
            "status": "started",
            "created_at": datetime.utcnow(),
            "steps_completed": [],
            "current_step": None,
            "result": None,
        }

        # Start execution in background
        asyncio.create_task(self._execute_workflow(workflow_id))

        return workflow_id

    async def _execute_workflow(self, workflow_id: str):
        """Execute workflow steps."""
        workflow = self._active_workflows.get(workflow_id)
        if not workflow:
            return

        try:
            workflow["status"] = "running"

            if workflow["type"] == "site_analysis":
                result = await self.orchestrator.run(workflow["request"])
                workflow["result"] = result
                workflow["status"] = "completed"

        except Exception as e:
            workflow["status"] = "failed"
            workflow["error"] = str(e)

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current workflow status."""
        return self._active_workflows.get(workflow_id)

    async def resume_workflow(self, workflow_id: str, decision: HumanDecision) -> bool:
        """Resume a workflow after human decision."""
        workflow = self._active_workflows.get(workflow_id)
        if not workflow or workflow["status"] != "awaiting_approval":
            return False

        workflow["human_decisions"] = workflow.get("human_decisions", [])
        workflow["human_decisions"].append(decision)
        workflow["status"] = "running"

        # Continue execution
        asyncio.create_task(self._execute_workflow(workflow_id))
        return True
