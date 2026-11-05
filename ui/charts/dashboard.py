import plotly.express as px
import plotly.graph_objects as go

COLORS=["#2563EB","#38BDF8","#16A34A","#F59E0B","#818CF8","#94A3B8"]
def base(fig):
    fig.update_layout(template="plotly_white",height=330,margin=dict(l=36,r=24,t=24,b=42),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(family="Inter, sans-serif",size=13,color="#334155"),legend=dict(orientation="h",y=1.12,x=0,font=dict(size=12)),hoverlabel=dict(bgcolor="#0F2747",font_color="#FFFFFF",bordercolor="#0F2747"))
    fig.update_xaxes(showline=False,zeroline=False,tickfont=dict(size=12,color="#52657D"),gridcolor="rgba(0,0,0,0)")
    fig.update_yaxes(showline=False,zeroline=False,tickfont=dict(size=12,color="#52657D"),gridcolor="#E8EEF6")
    return fig
def pipeline_chart(df):
    fig=go.Figure()
    for i,name in enumerate(["Pipeline Value","Weighted Pipeline"]):fig.add_trace(go.Scatter(x=df.month,y=df[name],name=name,mode="lines+markers",line=dict(color=COLORS[i],width=2.8,shape="spline"),marker=dict(size=6,line=dict(width=1,color="#fff")),fill="tozeroy" if i==0 else None,fillcolor="rgba(37,99,235,.07)",hovertemplate=f"<b>{name}</b><br>%{{x|%b %Y}}<br>€%{{y:,.0f}}<extra></extra>"))
    fig.update_yaxes(tickprefix="€",tickformat="~s");return base(fig)
def stage_chart(df):
    fig=px.pie(df,values="value",names="stage",hole=.62,color_discrete_sequence=COLORS)
    total=df.value.sum() if not df.empty else 0
    fig.update_traces(textposition="inside",textinfo="percent",textfont=dict(size=12),marker=dict(line=dict(color="#fff",width=2)),hovertemplate="<b>%{label}</b><br>€%{value:,.0f}<br>%{percent}<extra></extra>")
    fig.add_annotation(text=f"€{total/1_000_000:,.0f}M<br><span style='font-size:11px;color:#64748B'>total</span>",x=.5,y=.5,showarrow=False,font=dict(size=20,color="#10243A"))
    fig=base(fig);fig.update_layout(legend=dict(orientation="h",y=-.08,x=.5,xanchor="center",font=dict(size=11,color="#334155"),title=None),margin=dict(l=18,r=18,t=12,b=55));return fig
def region_chart(df):
    melted=df.melt("region",var_name="Metric",value_name="EUR")
    fig=px.bar(melted,x="region",y="EUR",color="Metric",barmode="group",color_discrete_sequence=COLORS[:2]);fig.update_traces(marker_line_width=0,hovertemplate="<b>%{x}</b><br>%{fullData.name}: €%{y:,.0f}<extra></extra>");fig.update_yaxes(tickprefix="€",tickformat="~s",title=None);fig.update_xaxes(title=None,tickangle=-18);return base(fig)
def quality_gauge(score):
    fig=go.Figure(go.Indicator(mode="gauge+number",value=score,number={"suffix":"%","font":{"size":42,"color":"#10243A"}},gauge={"shape":"angular","axis":{"range":[0,100],"tickwidth":0,"tickfont":{"size":11,"color":"#64748B"}},"bar":{"color":"#2563EB","thickness":.28},"bgcolor":"#EAF3FF","borderwidth":0,"steps":[{"range":[0,60],"color":"#FEF2F2"},{"range":[60,85],"color":"#FFFBEB"},{"range":[85,100],"color":"#ECFDF3"}]}));fig.update_layout(height=290,margin=dict(l=28,r=28,t=15,b=10),paper_bgcolor="rgba(0,0,0,0)",font=dict(family="Inter"));return fig
